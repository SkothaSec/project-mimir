import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

class MimirAlertGenerator:
    def __init__(self):
        # Use timezone-aware UTC for modern cloud compatibility
        self.base_time = datetime.now(timezone.utc)

    def _base_alert_builder(self, template: Dict[str, Any], offset_seconds: int = 0, **kwargs) -> Dict[str, Any]:
        """
        Creates a SIEM-style Alert Object.
        Unlike raw logs, these have 'severity', 'alert_name', and 'product'.
        """
        alert = template.copy()
        alert["alert_id"] = str(uuid.uuid4())
        
        # Calculate timestamp relative to start
        event_time = self.base_time + timedelta(seconds=offset_seconds)
        alert["timestamp"] = event_time.isoformat()
        
        # Default SIEM fields
        if "severity" not in alert: alert["severity"] = "Low"
        if "product" not in alert: alert["product"] = "Mimir Security Suite"
        if "status" not in alert: alert["status"] = "New"

        # Apply overrides
        alert.update(kwargs)
        return alert

    # =========================================================================
    # 1. ANCHORING GENERATOR (The "Alert Fatigue" Trap)
    # Goal: Overwhelm the analyst with "Low Severity" noise so they close the 
    # ticket before seeing the "High Severity" signal at the end.
    # =========================================================================
    def generate_anchoring_alerts(self, variant: str = "trap") -> List[Dict]:
        alerts = []
        user = "svc_backup_admin"
        src_ip = "10.50.1.100"

        # THE NOISE (The Anchor)
        # 8 "Low Severity" alerts. The analyst thinks: "Just a misconfigured password script."
        for i in range(8):
            alerts.append(self._base_alert_builder({
                "alert_name": "Authentication Failure",
                "severity": "Low",
                "description": f"Failed login attempt for {user} due to bad password.",
                "src_ip": src_ip,
                "user": user,
                "action": "Block"
            }, offset_seconds=i*2, test_case="Anchoring_Noise"))

        # THE SIGNAL (The contradictions)
        if variant == "trap":
            # The Trap: The 9th alert is SUCCESSFUL and HIGH severity, 
            # but looks similar enough to be ignored if skimming.
            alerts.append(self._base_alert_builder({
                "alert_name": "Privileged Account Login", # DIFFERENT NAME
                "severity": "High",                       # DIFFERENT SEVERITY
                "description": f"Successful login for {user}. New session established.",
                "src_ip": src_ip,
                "user": user,
                "action": "Allow"
            }, offset_seconds=20, test_case="Anchoring_Signal"))

        return alerts

    # =========================================================================
    # 2. APOPHENIA GENERATOR (The "False Pattern" Trap)
    # Goal: Create data that *looks* like a pattern (e.g. C2 Beaconing) 
    # but is mathematically random (Noise).
    # =========================================================================
    def generate_apophenia_alerts(self, variant: str = "trap") -> List[Dict]:
        alerts = []
        victim_ip = "192.168.1.55"
        
        if variant == "trap":
            # FALSE PATTERN (The Trap)
            # Random high ports, random intervals. 
            # Analyst sees "Many connections" -> assumes "Beacon".
            # Mimir must see "Random Math" -> asserts "Noise".
            
            # Random timestamps: 12s, 89s, 145s (No cadence)
            offsets = sorted([random.randint(0, 300) for _ in range(5)])
            
            for t in offsets:
                # Random ephemeral ports (looks like C2 jitter, but is just noise)
                rand_port = random.randint(49152, 65535)
                alerts.append(self._base_alert_builder({
                    "alert_name": "Outbound Network Connection",
                    "severity": "Medium",
                    "description": "Unusual outbound traffic detected to external IP.",
                    "src_ip": victim_ip,
                    "dest_ip": "203.0.113.88", # External
                    "dest_port": rand_port,    # RANDOM PORT
                    "bytes_out": random.randint(100, 5000) # RANDOM SIZE
                }, offset_seconds=t, test_case="Apophenia_FalsePattern"))

        elif variant == "truth":
            # TRUE PATTERN (The Signal)
            # Fixed 60s interval. Fixed Port. Fixed Byte Size.
            # This IS a pattern.
            for i in range(5):
                alerts.append(self._base_alert_builder({
                    "alert_name": "Outbound Network Connection",
                    "severity": "Medium",
                    "description": "Unusual outbound traffic detected to external IP.",
                    "src_ip": victim_ip,
                    "dest_ip": "203.0.113.88",
                    "dest_port": 8080, # FIXED PORT
                    "bytes_out": 256   # FIXED SIZE
                }, offset_seconds=i*60, test_case="Apophenia_TruePattern")) # FIXED INTERVAL

        return alerts

    # =========================================================================
    # 3. ABDUCTIVE GENERATOR (The "Missing Evidence" Gap)
    # Goal: Force the analyst to guess.
    # Mimir must identify that key fields (Parent Process) are null/missing.
    # =========================================================================
    def generate_abductive_alert(self, variant: str = "trap") -> List[Dict]:
        alerts = []
        
        # Base malicious-looking command
        cmd = "powershell.exe -nop -w hidden -enc JABzAD0A..."
        
        if variant == "trap":
            # THE TRAP: High Severity Alert, but MISSING CONTEXT.
            # We explicitly set parent_process to None or omit it.
            # Analyst Bias: "It's PowerShell, so it's malware."
            # Mimir Logic: "I cannot prove it's malware without the Parent."
            alerts.append(self._base_alert_builder({
                "alert_name": "Suspicious PowerShell Execution",
                "severity": "High",
                "description": "Encoded PowerShell command execution detected.",
                "user": "SYSTEM",
                "file_name": "powershell.exe",
                "command_line": cmd,
                "parent_process": None, # <--- THE MISSING EVIDENCE
                "parent_hash": None     # <--- THE MISSING EVIDENCE
            }, offset_seconds=5, test_case="Abductive_MissingEvidence"))

        elif variant == "truth":
            # THE TRUTH: Context provided.
            alerts.append(self._base_alert_builder({
                "alert_name": "Suspicious PowerShell Execution",
                "severity": "High",
                "description": "Encoded PowerShell command execution detected.",
                "user": "SYSTEM",
                "file_name": "powershell.exe",
                "command_line": cmd,
                "parent_process": "winword.exe", # <--- EVIDENCE PRESENT (Malicious)
                "parent_hash": "a1b2c3d4..."
            }, offset_seconds=5, test_case="Abductive_EvidencePresent"))

        return alerts

# Helper to run locally
if __name__ == "__main__":
    gen = MimirAlertGenerator()
    
    print("--- ANCHORING BATCH ---")
    print(json.dumps(gen.generate_anchoring_alerts("trap"), indent=2))
    
    print("\n--- APOPHENIA BATCH ---")
    print(json.dumps(gen.generate_apophenia_alerts("trap"), indent=2))

    print("\n--- ABDUCTIVE SINGLE ---")
    print(json.dumps(gen.generate_abductive_alert("trap"), indent=2))