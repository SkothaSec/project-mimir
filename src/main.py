import base64
import json
import os
import logging
import vertexai
from pathlib import Path
from flask import Flask, request
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
            analysis_target = json.dumps(input_data, indent=2)
        else:
            # Single (Abductive)
            log_id = input_data.get('alert_id', 'unknown')
            analysis_target = json.dumps(input_data, indent=2)
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
        "timestamp": input_data[0].get('timestamp') if isinstance(input_data, list) else input_data.get('timestamp'),
        "raw_log_summary": analysis_target,
        "bias_analysis": ai_analysis
    }]
    
    bq_client.insert_rows_json(TABLE_ID, rows)
    return "Analyzed", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))