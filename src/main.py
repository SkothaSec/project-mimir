import base64
import json
import os
import logging
import vertexai
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from google.cloud import bigquery
from vertexai.generative_models import GenerativeModel, SafetySetting

app = Flask(__name__)

# --- CONFIGURATION ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"
TABLE_ID = os.environ.get("BQ_TABLE_ID")

# Initialize Clients
bq_client = bigquery.Client()
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.5-pro")

# --- PROMPT LOADER ---
def load_system_prompt():
    try:
        base_dir = Path(__file__).parent
        prompt_path = base_dir / "prompts" / "system_prompt.md"
        if not prompt_path.exists():
            return "You are a security analyst."
        return prompt_path.read_text(encoding="utf-8")
    except Exception:
        return "You are a security analyst."

SYSTEM_INSTRUCTION = load_system_prompt()

REDACT_KEYS = {"test_case", "variant", "ground_truth", "label", "is_truth"}

def _redact_bias_hints(obj):
    """Remove keys that leak the intended scenario so Vertex must infer the bias."""
    if isinstance(obj, dict):
        return {k: _redact_bias_hints(v) for k, v in obj.items() if k not in REDACT_KEYS}
    if isinstance(obj, list):
        return [_redact_bias_hints(i) for i in obj]
    return obj

@app.route("/", methods=["POST"])
def index():
    envelope = request.get_json()
    if not envelope: return "no Pub/Sub message received", 400

    pubsub_message = envelope["message"]
    log_data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
    
    # Handle Batch vs Single
    try:
        input_data = json.loads(log_data_str)
        if isinstance(input_data, list):
            # Batch (Anchoring/Apophenia)
            log_id = f"batch_{input_data[0].get('alert_id', 'unknown')}"
            test_case = input_data[0].get("test_case")
            redacted = _redact_bias_hints(input_data)
            analysis_target = json.dumps(redacted, indent=2)
        else:
            # Single (Abductive)
            log_id = input_data.get('alert_id', 'unknown')
            test_case = input_data.get("test_case")
            redacted = _redact_bias_hints(input_data)
            analysis_target = json.dumps(redacted, indent=2)
    except:
        return "Invalid JSON", 400

    print(f"Analyzing Log ID: {log_id}")

    # CALL VERTEX AI
    try:
        chat = model.start_chat()
        response = chat.send_message(
            [SYSTEM_INSTRUCTION, f"ANALYZE THIS DATA:\n{analysis_target}"],
            generation_config={"response_mime_type": "application/json"}
        )
        # Clean markdown if present
        ai_analysis = response.text.strip()
        if ai_analysis.startswith("```json"):
            ai_analysis = ai_analysis[7:-3]
    except Exception as e:
        ai_analysis = json.dumps({"error": str(e)})

    # Insert into BigQuery
    rows = [{
        "log_id": log_id,
        "alert_group_id": input_data[0].get('alert_group_id') if isinstance(input_data, list) else input_data.get('alert_group_id'),
        "timestamp": input_data[0].get('timestamp') if isinstance(input_data, list) else input_data.get('timestamp'),
        "test_case": test_case,
        "raw_log_summary": analysis_target,
        "bias_analysis": ai_analysis
    }]
    
    bq_client.insert_rows_json(TABLE_ID, rows)
    return "Analyzed", 200

@app.route("/api/results", methods=["GET"])
def api_results():
    """Return latest analysis rows for the UI table."""
    query = f"""
    SELECT
      timestamp,
      JSON_VALUE(bias_analysis, '$.final_verdict') AS verdict,
      JSON_VALUE(bias_analysis, '$.verdict_confidence') AS verdict_confidence,
      JSON_VALUE(bias_analysis, '$.\"Notes for Analyst\"') AS notes,
      JSON_VALUE(bias_analysis, '$.apophenia_risk') AS apophenia,
      JSON_VALUE(bias_analysis, '$.anchoring_analysis') AS anchoring,
      JSON_VALUE(bias_analysis, '$.abductive_notes') AS abduction,
      raw_log_summary AS raw_logs,
      alert_group_id
    FROM `{TABLE_ID}`
    ORDER BY timestamp DESC
    LIMIT 5
    """
    rows = bq_client.query(query).result()
    payload = []
    for row in rows:
        payload.append({
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "verdict": row.verdict,
            "verdict_confidence": row.verdict_confidence,
            "notes": row.notes,
            "apophenia": row.apophenia,
            "anchoring": row.anchoring,
            "abduction": row.abduction,
            "raw_logs": row.raw_logs,
            "alert_group_id": row.alert_group_id,
        })
    return jsonify(payload)

@app.route("/ui", methods=["GET"])
def ui():
    """Serve built frontend (Vite build output)."""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        return "UI not built", 404
    return send_from_directory(frontend_dir, "index.html")

@app.route("/assets/<path:filename>")
def assets(filename):
    frontend_dir = Path(__file__).parent.parent / "frontend" / "assets"
    return send_from_directory(frontend_dir, filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
