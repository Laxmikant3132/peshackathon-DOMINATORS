import requests, json

payload = {
    "emailBody": (
        "Click here immediately to verify your account or it will be suspended:\n"
        "http://192.168.1.100/paypal-verify?token=abc123\n"
        "Also see: bit.ly/secure-login\n"
        "Your account has been blocked due to unusual activity. Enter your bank details and provide OTP to unlock.\n"
        "PayPal Security Team"
    ),
    "sender": "security-alert@paypa1-support.com",
    "subject": "URGENT: Account Suspended - Immediate Action Required",
    "headers": [
        {"name": "From", "value": "PayPal Security <security-alert@paypa1-support.com>"},
        {"name": "Reply-To", "value": "support@free-mail-harvester.ru"},
        {"name": "Return-Path", "value": "<bounces@paypa1-support.com>"},
        {"name": "Message-ID", "value": "<20250912.abc123@paypa1-support.com>"},
        {"name": "Received", "value": "from mail.paypa1-support.com (192.0.2.45) by mx.victim.com with SMTP; Fri, 12 Sep 2025 10:01:00 +0000"},
        {"name": "Received", "value": "from smtp.evil-relay.net (198.51.100.22) by mail.paypa1-support.com; Fri, 12 Sep 2025 09:58:00 +0000"},
        {"name": "Received", "value": "from unknown (203.0.113.77) by smtp.evil-relay.net; Fri, 12 Sep 2025 09:55:00 +0000"},
        {"name": "Authentication-Results", "value": "mx.victim.com; spf=fail; dkim=none; dmarc=fail"},
        {"name": "X-Spam-Status", "value": "Yes, score=9.5"},
    ],
    "attachments": [
        {"filename": "invoice.pdf.exe", "size_bytes": 204800, "mime_type": "application/octet-stream", "hash": "fakehash_for_test_abc123"},
    ],
}

try:
    resp = requests.post("http://localhost:8000/api/classify-email", json=payload, timeout=10)
    print("STATUS:", resp.status_code)
    data = resp.json()
    print("SAFETY:", data["safety"])
    print("CONFIDENCE:", data["confidence"])
    print("REASON:", data["reason"])
    print("INDICATORS COUNT:", len(data.get("indicators", [])))
    print()
    for ind in data.get("indicators", []):
        print(f"  [{ind['type']}] {ind['description'][:90]} (conf={ind['confidence']:.2f}, src={ind['source']})")
    print()
    print("FULL JSON:")
    print(json.dumps(data, indent=2))
except Exception as e:
    print("ERROR:", e)
