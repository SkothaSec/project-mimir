# src/main.py
import base64
import json
import os
from flask import Flask, request
from google.cloud import bigquery

app = Flask(__name__)
# Cap request size to mitigate abuse (1 MiB).
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

# BigQuery client is created once per process.
bq_client = bigquery.Client()

# Required env var (project.dataset.table). Fail fast if missing.
TABLE_ID = os.environ.get("BQ_TABLE_ID")
if not TABLE_ID:
    raise RuntimeError("BQ_TABLE_ID env var must be set to project.dataset.table")

def _validate_log(entry: dict) -> bool:
    """Lightweight schema validation for required fields."""
    required_fields = ["log_id", "timestamp"]
    if not isinstance(entry, dict):
        return False
    for field in required_fields:
        if field not in entry or not isinstance(entry[field], str) or not entry[field].strip():
            return False
    return True

@app.route("/", methods=["POST"])
def index():
    """Receive and process Pub/Sub messages."""
    envelope = request.get_json()
    if not envelope:
        return "no Pub/Sub message received", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        return "invalid Pub/Sub message format", 400

    # Decode the Log
    pubsub_message = envelope["message"]
    if not (isinstance(pubsub_message, dict) and "data" in pubsub_message):
        return "data missing", 400

    try:
        log_data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        log_entry = json.loads(log_data_str)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        # Bad base64 or JSON
        return f"invalid data: {exc}", 400

    if not _validate_log(log_entry):
        return "invalid log schema", 400

    print(f"Processing Log ID: {log_entry.get('log_id')}")

    # Call Vertex AI (Placeholder)
    # TODO: Insert your specific prompt logic here.
    # For now, we simulate a "success" response.
    mock_ai_response = {
        "anchoring_check": "No bias detected",
        "apophenia_risk": "Low",
        "reasoning": "Log appears benign."
    }

    # Insert into BigQuery
    rows_to_insert = [{
        "log_id": log_entry.get("log_id"),
        "timestamp": log_entry.get("timestamp"),
        "raw_log_summary": str(log_entry),
        "bias_analysis": json.dumps(mock_ai_response)
    }]

    errors = bq_client.insert_rows_json(TABLE_ID, rows_to_insert)
    if errors:
        print(f"Encountered errors while inserting rows: {errors}")
        return "BQ Error", 500

    return "Log Processed", 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
