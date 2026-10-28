"""
Live End-to-End API Pipeline Test for Raw EML Forensic Analysis.
Tests the actual /api/classify-email HTTP endpoint with the exact RFC 5322 EML sample.
Asserts:
- Parsed metadata (From, Reply-To, Return-Path, To, Subject, Date, Message-ID)
- Authentication-Results (SPF, DKIM, DMARC all FAIL)
- IP Classification (203.0.113.25 and 198.51.100.42 are Documentation / TEST-NET, NOT RFC1918)
- No header truncation (total headers >= 10, not 2)
- Consistent response for both raw_eml-only and client-parsed payload forms.
"""

import unittest
import requests
import json

LIVE_RAW_EML = """Received: from mail.example.net (203.0.113.25) by mx.victim.org with ESMTP; Sat, 12 Sep 2026 16:30:00 +0000

Received: from internal.example.net (198.51.100.42) by mail.example.net with SMTP; Sat, 12 Sep 2026 16:29:00 +0000

Authentication-Results: mx.victim.org; spf=fail smtp.mailfrom=security@example.net; dkim=fail header.i=@example.net; dmarc=fail action=none header.from=example.net
From: security@example.net
Reply-To: support@example.net
Return-Path: security@example.net
To: victim@example.org
Subject: URGENT: Your account will be suspended
Date: Sat, 12 Sep 2026 16:30:00 +0000
Message-ID: <urgent-test-123@example.net>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Your account will be suspended immediately. Please verify your credentials.
"""

API_URL = "http://localhost:8000/api/classify-email"


class TestLiveApiPipeline(unittest.TestCase):

    def test_live_api_raw_eml_exact_headers_and_auth(self):
        """Invoke live /api/classify-email and verify exact required fields."""
        payload = {
            "emailBody": "",
            "sender": "",
            "subject": "",
            "raw_eml": LIVE_RAW_EML,
        }

        resp = requests.post(API_URL, json=payload, timeout=15)
        self.assertEqual(resp.status_code, 200, f"API returned error: {resp.text}")
        data = resp.json()

        # 1. Parsed Metadata
        meta = data.get("parsed_metadata")
        self.assertIsNotNone(meta, "parsed_metadata missing in API response")
        self.assertEqual(meta.get("from"), "security@example.net")
        self.assertEqual(meta.get("reply_to"), "support@example.net")
        self.assertEqual(meta.get("return_path"), "security@example.net")
        self.assertEqual(meta.get("to"), "victim@example.org")
        self.assertEqual(meta.get("subject"), "URGENT: Your account will be suspended")
        self.assertEqual(meta.get("date"), "Sat, 12 Sep 2026 16:30:00 +0000")
        self.assertEqual(meta.get("message_id"), "<urgent-test-123@example.net>")

        # Header count must not be truncated to 2
        raw_headers = meta.get("raw_headers", [])
        self.assertGreaterEqual(len(raw_headers), 10, f"Expected >= 10 headers, got {len(raw_headers)}")

        # 2. Authentication-Results
        auth = data.get("authentication")
        self.assertIsNotNone(auth, "authentication missing in API response")
        self.assertEqual(auth.get("spf"), "FAIL", f"Expected SPF=FAIL, got {auth.get('spf')}")
        self.assertEqual(auth.get("dkim"), "FAIL", f"Expected DKIM=FAIL, got {auth.get('dkim')}")
        self.assertEqual(auth.get("dmarc"), "FAIL", f"Expected DMARC=FAIL, got {auth.get('dmarc')}")

        # 3. IP Classification
        hops = data.get("relay_hops", [])
        self.assertGreaterEqual(len(hops), 2, "Expected at least 2 hops")

        hop_ips = {h.get("from_ip"): h for h in hops if h.get("from_ip")}
        self.assertIn("203.0.113.25", hop_ips, "Hop 203.0.113.25 not extracted")
        self.assertIn("198.51.100.42", hop_ips, "Hop 198.51.100.42 not extracted")

        for test_ip in ["203.0.113.25", "198.51.100.42"]:
            hop = hop_ips[test_ip]
            ip_class = hop.get("ip_classification") or {}
            category = ip_class.get("category")
            label = ip_class.get("label", "")

            # MUST be Documentation / TEST-NET
            self.assertEqual(category, "documentation_test_net", f"{test_ip} classified as {category}")
            self.assertIn("Documentation / TEST-NET", label, f"{test_ip} label is {label}")

            # MUST NOT be RFC1918
            self.assertNotEqual(category, "rfc1918_private", f"{test_ip} incorrectly classified as RFC1918")
            self.assertNotIn("RFC1918", label, f"{test_ip} label mentions RFC1918: {label}")
            self.assertFalse(hop.get("is_public"), f"{test_ip} should not be publicly routable")

        # 4. Diagnostics
        diag = data.get("diagnostics", {})
        self.assertGreaterEqual(diag.get("num_headers", 0), 10, "Diagnostics num_headers truncated")

    def test_live_api_browser_payload_form(self):
        """Invoke live API with the exact payload structure sent by the browser."""
        payload = {
            "emailBody": "Your account will be suspended immediately.",
            "sender": "security@example.net",
            "subject": "URGENT: Your account will be suspended",
            "headers": [
                {"name": "Received", "value": "from mail.example.net (203.0.113.25) by mx.victim.org"},
                {"name": "Received", "value": "from internal.example.net (198.51.100.42) by mail.example.net"},
            ],
            "raw_eml": LIVE_RAW_EML,
        }

        resp = requests.post(API_URL, json=payload, timeout=15)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Ensure raw_eml headers take precedence over truncated browser headers list
        meta = data.get("parsed_metadata", {})
        self.assertEqual(meta.get("from"), "security@example.net")
        self.assertEqual(meta.get("reply_to"), "support@example.net")
        self.assertGreaterEqual(len(meta.get("raw_headers", [])), 10)

        auth = data.get("authentication", {})
        self.assertEqual(auth.get("spf"), "FAIL")
        self.assertEqual(auth.get("dkim"), "FAIL")
        self.assertEqual(auth.get("dmarc"), "FAIL")


if __name__ == "__main__":
    unittest.main()
