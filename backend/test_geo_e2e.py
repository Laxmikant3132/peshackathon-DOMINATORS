import requests
import json
import os

# Realistic Synthetic EML payload with:
# - Multi-hop Received headers
# - Earliest observable public routable IP: 8.8.8.8 (Google Public DNS infrastructure)
# - Intermediate private and documentation hops
payload = {
    "emailBody": (
        "Security Alert: Your payment session timed out.\n"
        "Please re-authenticate your credentials immediately: https://192.168.1.1/login\n"
        "Help desk reference: #SEC-9912."
    ),
    "sender": "security@alert-service.com",
    "subject": "Action Required: Session Timeout",
    "headers": [
        {"name": "From", "value": "Security Team <security@alert-service.com>"},
        {"name": "Reply-To", "value": "security@alert-service.com"},
        # Top hop (destination MX receiving internally)
        {"name": "Received", "value": "from internal-relay.local (10.0.1.20) by mx.victim.com with SMTP; Fri, 12 Sep 2025 12:00:00 +0000"},
        # Intermediate relay
        {"name": "Received", "value": "from mail-out.provider.net (192.168.10.5) by internal-relay.local with ESMTP; Fri, 12 Sep 2025 11:58:00 +0000"},
        # Earliest public originating relay hop (8.8.8.8)
        {"name": "Received", "value": "from mail.sender-org.com (mail.sender-org.com [8.8.8.8]) by mail-out.provider.net with ESMTP; Fri, 12 Sep 2025 11:55:00 +0000"},
        # Client submission behind RFC 1918 NAT
        {"name": "Received", "value": "from [172.16.0.4] by mail.sender-org.com with HTTP; Fri, 12 Sep 2025 11:50:00 +0000"}
    ]
}

print("=== 1. Test Without IPINFO_TOKEN (Should show UNAVAILABLE) ===")
try:
    resp = requests.post("http://localhost:8000/api/classify-email", json=payload, timeout=5)
    print("Status:", resp.status_code)
    geo = resp.json().get("geolocation")
    print("Geolocation output:", json.dumps(geo, indent=2))
except Exception as e:
    print("Error:", e)
