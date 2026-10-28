import requests
import json
import os
from unittest.mock import patch, MagicMock

payload_all_private = {
    "emailBody": "Meeting reminder.",
    "sender": "boss@company.internal",
    "subject": "Quick sync",
    "headers": [
        {"name": "Received", "value": "from internal (10.0.0.1) by mx.internal (192.168.1.1)"},
        {"name": "Received", "value": "from pc (127.0.0.1) by internal (192.0.2.1)"}
    ]
}

# 1. Test when only private/doc IPs exist in Received
resp1 = requests.post("http://localhost:8000/api/classify-email", json=payload_all_private, timeout=5)
geo1 = resp1.json().get("geolocation")
print("=== All Private/Doc IPs Result ===")
print("State:", geo1.get("provider_state"))
print("IP:", geo1.get("ip"))
print("Error:", geo1.get("error"))
assert geo1.get("provider_state") == "UNKNOWN"
assert geo1.get("error") == "No reliable public originating IP available"

print("\nAll Private Check Passed!")
