import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

class MimirMatrix:
    def __init__(self):
        """Capture start time so all logs are relative to this."""
        self.base_time = datetime.now(timezone.utc)    
    def _base_log_builder(self, template: Dict[str, Any], offset_seconds: int = 0, **kwargs) -> Dict[str, Any]:
        """
        Creates a single stadardized log entry based on a template and additional parameters.
        Args:
            template: A dictionary containing default values for the log type.
            offset_seconds: How many seconds after the simulations starts this event occurs
            **kwargs: overrides to change specific fields in the log entry.
        """
        event = template.copy() # Create copy so original template is not modified
        event["log_id"] = str(uuid.uuid4()) # Unique identifier for the log entry
        event_time = self.base_time + timedelta(seconds=offset_seconds) # Calculate event time
        event["timestamp"] = event_time.isoformat() + "Z" # ISO 8601 format with Zulu timezone
        event.update(kwargs) # Override with any additional parameters
        return event

    # Place holder for additional methods to generate specific log types
    def generate_anchoring(self):
        pass
    
    def generate_apophenia(self, variant: str = "trap") -> list:
        """
        Generates logs for an apophenia trap, truth, and uncertain scenario.
        The end result will be coincicence (Noise) and a true positive (Signal).
        :param variant: The type of apophenia scenario to generate. Options are "trap", "truth", and "uncertain".
        :type variant: str
        :param self: Description
        :return: Description
        :rtype: list
        """
        # Need a consistent dst_port and an external dst_ip for all events in the scenario
        sequence = []

        if variant == "trap":
            # NOICE: Messy CDN domains, ranom length and chars.
            # Not a tunnel, just messy traffic
            for i in range(5):
                rand_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(5,15)))
                domain = f"content-{rand_str}.akamai.net"
                sequence.append(self._base_log_builder({
                    "event_type": "dns_query",
                    "query": domain,
                    "query_type": "A",
                    "proc": "chrome.exe",
                }, offset_seconds=i*10, test_case = "T1071_Apophenia"))
        elif variant == "truth":
            # SIGNAL: Sequential exfiltration to a known C2 domain
            # The data is random, but the STRUCTURE is ordered (chunk1, chunk2...)
            # Or the size is suspiciously uniform.
            exfil_id = "a1b2"
            for i in range(5):
                # simulated base64 data chunk
                chunk = f"data_chunk_{i}_of_5_payload_{exfil_id}"
                domain = f"{chunk}.bad-c2.io"
                sequence.append(self._base_log_builder({
                    "event_type": "dns_query",
                    "query": domain,
                    "query_type": "TXT", # common for tunneling
                    "proc": "powershell.exe", # sus process for DNS tunneling
                }, offset_seconds=i*10 + 60, test_case = "T1071_Apophenia"))
        elif variant == "uncertain":
            # MIXED: Random DNS queries with some suspicious patterns
            for i in range(10):
                if i % 3 == 0:
                    # Suspicious chunked data
                    chunk = f"data_chunk_{i//3}_of_4_payload_xyz"
                    domain = f"{chunk}.suspicious-domain.com"
                    sequence.append(self._base_log_builder({
                        "event_type": "dns_query",
                        "query": domain,
                        "query_type": "TXT",
                        "proc": "cmd.exe",
                    }, offset_seconds=i*10 + 120, test_case = "T1071_Apophenia"))
                else:
                    # Random noise
                    rand_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(5,15)))
                    domain = f"random-{rand_str}.example.com"
                    sequence.append(self._base_log_builder({
                        "event_type": "dns_query",
                        "query": domain,
                        "query_type": "A",
                    "proc": "firefox.exe",
                }, offset_seconds=i*10 + 120, test_case = "T1071_Apophenia"))
        return sequence

    def generate_abduction(self):
        pass

if __name__ == "__main__":
    generator = MimirMatrix()

    # Dummy template for testing
    ssh_template = {
        "event_type": "ssh_login",
        "user": "unknown",
        "src_ip": "192.168.1.100",
        "dst_ip": "192.168.1.1",
        "status": "FAILURE"
    }

    #test_log = generator._base_log_builder(ssh_template, offset_seconds=5, user="admin", status="SUCCESS")
    apophenia_logs = generator.generate_apophenia(variant="trap")
    print(json.dumps(apophenia_logs, indent=4))
