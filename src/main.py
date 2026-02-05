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
model = GenerativeModel("gemini-1.5-pro-001")

# --- PROMPT LOADER ---
def load_system_prompt():
    """Loads the markdown system prompt from src/prompts/system_prompt.md"""
    try:
        base_dir = Path(__file__).parent
        prompt_path = base_dir / "prompts" / "system_prompt.md"
        
        if not prompt_path.exists():
            print(f"WARNING: Prompt file not found at {prompt_path}. Using fallback.")
            return "You are a security analyst. Analyze the following logs for bias."
            
        print(f"Loaded System Prompt from: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")
        
    except Exception as e:
        print(f"ERROR loading prompt: {e}")
        return "You are a security analyst."

# Load Prompt Logic
SYSTEM_INSTRUCTION = load_system_prompt()

@app.route("/", methods=["POST"])
def index():
    """
    Ingests Pub/Sub messages containing SIEM Alerts.
    Handles both SINGLE alerts (Abductive) and BATCH alerts (Anchoring/Apophenia).
    """
    envelope = request.get_json()
    if not envelope:
        return "no Pub/Sub message received", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        return "invalid Pub/Sub message format", 400

    # Decode the Payload
    pubsub_message = envelope["message"]
    if isinstance(pubsub_message, dict) and "data" in pubsub_message:
        try:
            log_data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
            input_data = json.loads(log_data_str)
        except Exception as e:
            print(f"JSON Decode Error: {e}")
            return "Invalid JSON", 400
    else:
        return "data missing", 400

    # Determine Context (Batch vs Single)
    # The generator sends a LIST for Anchoring/Apophenia, but a DICT for single events.
    if isinstance(input_data, list):
        # It's a BATCH. We need to analyze the specific sequence.
        # We use the first event's ID as the "Batch ID" for tracking.
        log_id = f"batch_{input_data[0].get('alert_id', 'unknown')}"
        timestamp = input_data[0].get('timestamp')
        analysis_target = json.dumps(input_data, indent=2) # Send the whole list to AI
        print(f"Processing Batch of {len(input_data)} alerts. ID: {log_id}")
        
    else:
        # It's a SINGLE alert.
        log_id = input_data.get('alert_id', input_data.get('log_id', 'unknown'))
        timestamp = input_data.get('timestamp')
        analysis_target = json.dumps(input_data, indent=2)
        print(f"Processing Single Alert. ID: {log_id}")

    # CALL VERTEX AI (The Cognitive Filter)
    try:
        # We start a chat session to maintain context, though for single request it's stateless
        chat = model.start_chat()
        
        # The User Prompt simply presents the data
        response = chat.send_message(
            [SYSTEM_INSTRUCTION, f"ANALYZE THIS DATA:\n{analysis_target}"],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Clean response
        ai_analysis_json = response.text.strip()
        if ai_analysis_json.startswith("```json"):
            ai_analysis_json = ai_analysis_json[7:-3]

    except Exception as e:
        print(f"Vertex AI Error: {e}")
        ai_analysis_json = json.dumps({"error": str(e), "verdict": "ERROR"})

    # Save to BigQuery
    # We store the inputs (raw logs) and the outputs (AI analysis) side-by-side.
    rows_to_insert = [{
        "log_id": log_id,
        "timestamp": timestamp,
        "raw_log_summary": analysis_target, # Stores the full batch or single log
        "bias_analysis": ai_analysis_json
    }]

    errors = bq_client.insert_rows_json(TABLE_ID, rows_to_insert)
    if errors:
        print(f"BQ Insert Errors: {errors}")
        return "BQ Error", 500

    return "Analyzed", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))