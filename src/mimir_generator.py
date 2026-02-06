import json
import uuid
import random
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from google.cloud import pubsub_v1

class MimirAlertGenerator:
    def __init__(self, project_id: str = None, topic_id: str = "mimir-ingest-topic"):
        self.base_time = datetime.now(timezone.utc)
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.topic_id = topic_id

    def _base_alert_builder(self, template: Dict[str, Any], offset_seconds: int = 0, group_id: str = None, **kwargs) -> Dict[str, Any]:
        """Creates a standardized SIEM alert object."""
        alert = template.copy()
        alert["log_id"] = str(uuid.uuid4())
        alert["alert_id"] = str(uuid.uuid4())
        if group_id:
            alert["alert_group_id"] = group_id
        event_time = self.base_time + timedelta(seconds=offset_seconds)
        alert["timestamp"] = event_time.isoformat()
        
        # Default fields if not provided
        if "severity" not in alert: alert["severity"] = "Low"
        if "product" not in alert: alert["product"] = "Mimir Security Suite"
        
        alert.update(kwargs)
        return alert

    # --- 1. ANCHORING (Alert Fatigue) ---
    def generate_anchoring(self, variant: str = "trap") -> List[Dict]:
        alerts = []
        group_id = str(uuid.uuid4())
        user = "svc_backup"
        src_ip = "10.50.1.100"

        # NOISE: 12 Low severity alerts (The Anchor)
        for i in range(12):
            alerts.append(self._base_alert_builder({
                "alert_name": "Authentication Failure",
                "severity": "Low",
                "description": f"Failed login for {user}. Likely bad script.",
                "src_ip": src_ip,
                "user": user,
                "action": "Block"
            }, offset_seconds=i*5, group_id=group_id, test_case="Anchoring_Noise"))

        # SIGNAL: The high severity event hidden at the end
        if variant == "trap":
            alerts.append(self._base_alert_builder({
                "alert_name": "Privileged Account Login",
                "severity": "High",
                "description": f"Successful login for {user}. Session established.",
                "src_ip": src_ip,
                "user": user,
                "action": "Allow"
            }, offset_seconds=70, group_id=group_id, test_case="Anchoring_Signal"))
            
        return alerts

    # --- 2. APOPHENIA (False Patterns) ---
    def generate_apophenia(self, variant: str = "trap") -> List[Dict]:
        alerts = []
        group_id = str(uuid.uuid4())
        victim_ip = "192.168.1.55"
        
        if variant == "trap":
            # TRAP: Random intervals, random ports. NOISE.
            # Analyst sees "Beaconing", Mimir sees "Randomness".
            offsets = sorted([random.randint(0, 420) for _ in range(10)])
            for t in offsets:
                alerts.append(self._base_alert_builder({
                    "alert_name": random.choice(["Outbound Connection","DNS Query","HTTPS Request"]),
                    "severity": random.choice(["Low","Medium"]),
                    "description": "Random outbound traffic.",
                    "src_ip": victim_ip,
                    "dest_ip": random.choice(["203.0.113.88","198.51.100.42","192.0.2.77"]),
                    "dest_port": random.randint(49152, 65535), # Random Port
                    "bytes_out": random.randint(100, 8000)     # Random Size
                }, offset_seconds=t, group_id=group_id, test_case="Apophenia_Trap"))

        elif variant == "truth":
            # TRUTH: Fixed interval (60s), fixed port. SIGNAL.
            for i in range(8):
                alerts.append(self._base_alert_builder({
                    "alert_name": "Outbound Connection",
                    "severity": "Medium",
                    "description": "Suspicious outbound traffic.",
                    "src_ip": victim_ip,
                    "dest_ip": "203.0.113.88",
                    "dest_port": 8080, # Fixed Port
                    "bytes_out": 256   # Fixed Size
                }, offset_seconds=i*60, group_id=group_id, test_case="Apophenia_Truth"))
                
        return alerts

    # --- 3. ABDUCTIVE (Missing Evidence) ---
    def generate_abductive(self, variant: str = "trap") -> List[Dict]:
        alerts = []
        group_id = str(uuid.uuid4())
        cmd = "powershell.exe -nop -w hidden -enc JABzAD0A..."
        
        if variant == "trap":
            # TRAP: Missing Parent Process.
            for i in range(3):
                alerts.append(self._base_alert_builder({
                    "alert_name": "Suspicious PowerShell",
                    "severity": "High",
                    "description": "Encoded PowerShell detected.",
                    "user": "SYSTEM",
                    "file_name": "powershell.exe",
                    "command_line": cmd,
                    "parent_process": None, # <--- MISSING EVIDENCE
                }, offset_seconds=5 + i*30, group_id=group_id, test_case="Abductive_Trap"))
            
        return alerts

    def publish(self, data: List[Dict]):
        """Publishes the entire batch as one Pub/Sub message (batch analysis)."""
        if not self.project_id:
            print("ERROR: GOOGLE_CLOUD_PROJECT env var not set.")
            return

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(self.project_id, self.topic_id)

        message_bytes = json.dumps(data).encode("utf-8")
        try:
            future = publisher.publish(topic_path, message_bytes)
            future.result()
            print(f"Sent 1 batch ({len(data)} alerts) to {self.topic_id}")
        except Exception as e:
            print(f"Failed to publish batch: {e}")

if __name__ == "__main__":
    # ARGUMENT PARSER (The CLI Interface)
    parser = argparse.ArgumentParser(description="Generate and Send Mimir Test Data")
    parser.add_argument("type", choices=["anchoring", "apophenia", "abduction"], help="What to test")
    parser.add_argument("--variant", choices=["trap", "truth"], default="trap", help="Scenario variant")
    parser.add_argument("--send", action="store_true", help="Send directly to Pub/Sub")
    parser.add_argument("--project", help="GCP Project ID")
    
    args = parser.parse_args()

    # Initialize
    gen = MimirAlertGenerator(project_id=args.project)
    
    # Generate Data
    data = []
    if args.type == "anchoring":
        data = gen.generate_anchoring(args.variant)
    elif args.type == "apophenia":
        data = gen.generate_apophenia(args.variant)
    elif args.type == "abduction":
        data = gen.generate_abductive(args.variant)

    # Output
    if args.send:
        gen.publish(data)
    else:
        print(json.dumps(data, indent=2))
