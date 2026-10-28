"""
Comprehensive End-to-End Pipeline Test with a Realistic Synthetic EML:
- Multi-hop Received headers (including private and public IPs)
- Authentication-Results with SPF, DKIM, DMARC
- ARC-Authentication-Results (ARC chain)
- From/Reply-To mismatch (From: PayPal Security, Reply-To: attacker)
- Lookalike sender domain (paypa1-security.com)
- Display name impersonation
- Phishing body language (Account Suspension, Credential Harvesting, Urgency)
- Multiple URLs (IP-based URL, Shortener, Normal URL)
- Suspicious attachment metadata (double extension .pdf.exe)
"""

import unittest
from services.email_forensics_pipeline import (
    parse_full_email,
    extract_all_urls,
    analyze_url_forensics,
    analyze_origin_trace,
    parse_authentication_results,
    analyze_sender_forensics,
    analyze_body_nlp,
    calculate_explainable_risk
)

SYNTHETIC_RAW_EML = """Received: from mail-relay.victim.com (10.0.0.1) by mx.victim.com with SMTP; Fri, 12 Sep 2025 10:05:00 +0000
Received: from mail.gateway.net (192.168.1.50) by mail-relay.victim.com with ESMTP; Fri, 12 Sep 2025 10:02:00 +0000
Received: from mail.paypa1-security.com (mail.paypa1-security.com [93.184.216.34]) by mail.gateway.net with ESMTPS (TLS1.3); Fri, 12 Sep 2025 10:00:00 +0000
From: "PayPal Security Team" <security-alert@paypa1-security.com>
To: victim@company.com
Reply-To: credential-collector@harvest-box.ru
Return-Path: <bounces@paypa1-security.com>
Subject: URGENT: Account Suspended - Immediate Action Required
Date: Fri, 12 Sep 2025 10:00:00 +0000
Message-ID: <202509121000.abc12345@paypa1-security.com>
Authentication-Results: mx.victim.com; spf=fail smtp.mailfrom=paypa1-security.com; dkim=fail header.i=@paypa1-security.com; dmarc=fail
ARC-Authentication-Results: i=1; mx.google.com; spf=pass; dkim=pass; dmarc=pass
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="BOUNDARY_XYZ_123"

--BOUNDARY_XYZ_123
Content-Type: text/plain; charset="utf-8"

Your account has been blocked due to suspicious activity.
Re-authenticate and enter your password immediately or your account will be permanently closed:
http://192.168.1.100/paypal-login
Also check: https://bit.ly/secure-portal-verify
Customer Support: https://help.paypal.com/contact

--BOUNDARY_XYZ_123
Content-Type: application/octet-stream; name="account_statement.pdf.exe"
Content-Disposition: attachment; filename="account_statement.pdf.exe"
Content-Transfer-Encoding: base64

TVqQAAMAAAAEAAAA//8AALgAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAA==
--BOUNDARY_XYZ_123--
"""

class TestSyntheticForensicPipeline(unittest.TestCase):

    def test_full_pipeline_synthetic_eml(self):
        # 1. Parse full email
        parsed = parse_full_email(SYNTHETIC_RAW_EML)
        self.assertIn("PayPal Security Team", parsed["from"])
        self.assertIn("security-alert@paypa1-security.com", parsed["from"])
        self.assertEqual(parsed["reply_to"], "credential-collector@harvest-box.ru")
        self.assertEqual(len(parsed["attachments"]), 1)
        self.assertEqual(parsed["attachments"][0]["filename"], "account_statement.pdf.exe")
        self.assertIsNotNone(parsed["attachments"][0]["hash"])

        # 2. Extract and analyze URLs
        urls = parsed["urls"]
        self.assertTrue(any("192.168.1.100" in u for u in urls))
        self.assertTrue(any("bit.ly" in u for u in urls))
        
        url_analyses = [analyze_url_forensics(u) for u in urls]
        ip_url_found = any(u["is_ip"] for u in url_analyses)
        shortener_found = any(u["is_shortener"] for u in url_analyses)
        self.assertTrue(ip_url_found)
        self.assertTrue(shortener_found)

        # 3. Authentication Forensics
        auth = parse_authentication_results(parsed["headers"], "paypa1-security.com")
        self.assertEqual(auth["spf"], "FAIL")
        self.assertEqual(auth["dkim"], "FAIL")
        self.assertEqual(auth["dmarc"], "FAIL")
        self.assertTrue(auth["has_arc"])
        self.assertIsNotNone(auth["arc_results"])

        # 4. Sender Forensics
        sender_findings = analyze_sender_forensics(parsed["from"], parsed["reply_to"], parsed["return_path"], parsed["plain_body"])
        has_reply_mismatch = any("Reply-To Domain Mismatch" in f["description"] for f in sender_findings)
        has_lookalike = any("Lookalike domain" in f["description"] for f in sender_findings)
        has_display_impersonation = any("Display Name Impersonation" in f["description"] for f in sender_findings)
        self.assertTrue(has_reply_mismatch)
        self.assertTrue(has_lookalike)
        self.assertTrue(has_display_impersonation)

        # 5. Body NLP Forensics
        nlp_findings = analyze_body_nlp(parsed["subject"], parsed["plain_body"])
        has_suspension = any("Account Suspension" in f["description"] for f in nlp_findings)
        has_credential = any("Credential Harvesting" in f["description"] for f in nlp_findings)
        has_urgency = any("Urgency" in f["description"] for f in nlp_findings)
        self.assertTrue(has_suspension)
        self.assertTrue(has_credential)
        self.assertTrue(has_urgency)

        # 6. Origin Trace
        received_headers = [h["value"] for h in parsed["headers"] if h["name"].lower() == "received"]
        hops, earliest_public = analyze_origin_trace(received_headers)
        self.assertEqual(len(hops), 3)
        self.assertIsNotNone(earliest_public)
        self.assertEqual(earliest_public["from_ip"], "93.184.216.34")
        self.assertTrue(earliest_public["is_public"])

        # 7. Explainable Risk Score
        all_findings = sender_findings + nlp_findings
        risk = calculate_explainable_risk(all_findings, auth, None, parsed["attachments"])
        self.assertEqual(risk["safety"], "dangerous")
        self.assertGreaterEqual(risk["score"], 80)
        self.assertGreaterEqual(len(risk["factors"]), 4)

if __name__ == "__main__":
    unittest.main()
