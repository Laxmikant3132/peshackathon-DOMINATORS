"""
Comprehensive Email Threat Detection, GeoLocation & Forensic Intelligence test suite.
Covers: NLP/AI threat detection, email forensics, origin traceability, infrastructure
intelligence, domain intelligence, threat intelligence, attribution support, graph
correlation, geolocation, real-time pipeline, dashboard data, forensic evidence,
case management, chain of custody, privacy/compliance, forensic reporting,
attachment forensics.

External providers are NEVER mocked with fake intelligence: tests use the real
provider contract (Unavailable when unconfigured) and monkeypatch only the HTTP
boundary where a controlled real-shaped response is required.

Run: python -m unittest tests.test_email_forensics_comprehensive -v
"""
import os
import sys
import json
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

PHISH_HEADERS = [
    {"name": "From", "value": "PayPal Security <security@paypa1-verify.com>"},
    {"name": "To", "value": "victim@example.com"},
    {"name": "Reply-To", "value": "attacker@gmail.com"},
    {"name": "Return-Path", "value": "<bounce@evil-relay.net>"},
    {"name": "Message-ID", "value": "<phish001@evil-relay.net>"},
    {"name": "Date", "value": "Fri, 12 Sep 2025 10:00:00 +0000"},
    {"name": "Subject", "value": "URGENT: Account suspended - verify immediately"},
    {"name": "Authentication-Results", "value": "mx.victim.com; spf=fail smtp.mailfrom=evil-relay.net; dkim=none; dmarc=fail"},
    {"name": "Received", "value": "from mail.victim.com (10.0.0.2) by mx.victim.com; Fri, 12 Sep 2025 10:01:00 +0000"},
    {"name": "Received", "value": "from smtp.evil-relay.net (198.51.100.22) by mail.victim.com; Fri, 12 Sep 2025 10:00:30 +0000"},
    {"name": "Received", "value": "from unknown (93.184.216.34) by smtp.evil-relay.net; Fri, 12 Sep 2025 10:00:00 +0000"},
]

PHISH_BODY = """
Dear customer,

Your account will be permanently suspended within 24 hours unless you verify your password now.
Click here to unlock: http://198.51.100.5/verify-login?u=encrypted
Enter your bank details and confirm your pin to restore access.

Urgent action required. Final notice.
"""

SAFE_HEADERS = [
    {"name": "From", "value": "Team Updates <no-reply@github.com>"},
    {"name": "To", "value": "analyst@example.com"},
    {"name": "Message-ID", "value": "<ok001@github.com>"},
    {"name": "Date", "value": "Fri, 12 Sep 2025 09:00:00 +0000"},
    {"name": "Subject", "value": "Weekly digest"},
    {"name": "Authentication-Results", "value": "mx.victim.com; spf=pass; dkim=pass; dmarc=pass"},
    {"name": "Received", "value": "from out.github.com (140.82.112.3) by mx.victim.com; Fri, 12 Sep 2025 09:00:00 +0000"},
]
SAFE_BODY = "Here is your weekly repository digest. No action required."


class ForensicTestBase(unittest.TestCase):
    client = None
    tmpdir = None
    orig_store = None

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("FORENSIC_TEST_MODE", "1")
        import main as backend_main
        from services import case_store, privacy
        cls.main_mod = backend_main
        cls.case_store = case_store
        cls.privacy = privacy
        # Redirect stores to a temp dir so tests never touch real case data
        cls.tmpdir = tempfile.mkdtemp(prefix="fw-test-")
        cls.orig_store = case_store._STORE_PATH
        cls.orig_audit = privacy._AUDIT_PATH
        cls.orig_cfg = privacy._CONFIG_PATH
        case_store._STORE_PATH = os.path.join(cls.tmpdir, "cases.json")
        privacy._AUDIT_PATH = os.path.join(cls.tmpdir, "audit.jsonl")
        privacy._CONFIG_PATH = os.path.join(cls.tmpdir, "privacy.json")
        cls.client = TestClient(backend_main.app)

    @classmethod
    def tearDownClass(cls):
        cls.case_store._STORE_PATH = cls.orig_store
        cls.privacy._AUDIT_PATH = cls.orig_audit
        cls.privacy._CONFIG_PATH = cls.orig_cfg
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def analyze_phish(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": PHISH_BODY, "sender": "security@paypa1-verify.com",
            "subject": "URGENT: Account suspended - verify immediately",
            "headers": PHISH_HEADERS,
        })
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def analyze_safe(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": SAFE_BODY, "sender": "no-reply@github.com",
            "subject": "Weekly digest", "headers": SAFE_HEADERS,
        })
        self.assertEqual(resp.status_code, 200)
        return resp.json()


# ===========================================================================
# 1. AI/NLP threat detection
# ===========================================================================
class TestNLPThreatDetection(ForensicTestBase):
    def test_phishing_urgency_credential_harvesting_detected(self):
        res = self.analyze_phish()
        descs = [f["description"].lower() for f in res["indicators"]]
        self.assertTrue(any("credential harvesting" in d for d in descs), f"missing: {descs[:8]}")
        self.assertTrue(any("urgency" in d for d in descs), "urgency missing")
        self.assertTrue(any("suspension" in d for d in descs))

    def test_bec_payment_diversion_detection(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": "Hi, I'm in a meeting with the CEO. Please process the attached invoice for immediate payment via wire transfer. New wire instructions below.",
            "sender": "cfo@company-finance.net", "subject": "Re: payment", "headers": [],
        })
        descs = " ".join(f["description"].lower() for f in resp.json()["indicators"])
        self.assertIn("bec", descs)
        self.assertIn("invoice", descs)

    def test_deceptive_language_and_generic_salutation(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": "Dear valued customer, I hope this email finds you well. Kindly confirm your identity immediately.",
            "sender": "support@unknown-brand.xyz", "subject": "Notice", "headers": [],
        })
        descs = " ".join(f["description"].lower() for f in resp.json()["indicators"])
        self.assertIn("templated", descs)
        self.assertIn("salutation", descs)

    def test_lookalike_display_name_impersonation(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": PHISH_BODY,
            "sender": "PayPal Security <security@paypa1-verify.com>",
            "subject": "URGENT: Account suspended - verify immediately",
            "headers": PHISH_HEADERS,
        })
        descs = " ".join(f["description"].lower() for f in resp.json()["indicators"])
        self.assertIn("lookalike", descs)
        self.assertIn("display name impersonation", descs)

    def test_homoglyph_punycode_sender(self):
        from services.email_forensics_pipeline import analyze_homoglyph_domain
        f = analyze_homoglyph_domain("xn--paypa-3ve.com")
        self.assertTrue(any("punycode" in x["description"].lower() for x in f))
        f2 = analyze_homoglyph_domain("paypa1.com")
        self.assertTrue(any("normalizes" in x["description"].lower() or "confusable" in x["description"].lower() for x in f2))

    def test_malicious_ip_url_flagged(self):
        res = self.analyze_phish()
        descs = " ".join(f["description"].lower() for f in res["indicators"])
        self.assertIn("ip-based", descs)

    def test_safe_email_not_dangerous(self):
        res = self.analyze_safe()
        self.assertEqual(res["safety"], "safe")

# ===========================================================================
# 2. Complete email forensics
# ===========================================================================
class TestEmailForensics(ForensicTestBase):
    def test_raw_mime_parsing_metadata(self):
        raw = (
            "From: PayPal Security <security@paypa1-verify.com>\r\n"
            "To: victim@example.com\r\nCc: audit@example.com\r\n"
            "Reply-To: attacker@gmail.com\r\nReturn-Path: <bounce@evil-relay.net>\r\n"
            "Message-ID: <raw001@evil>\r\nDate: Fri, 12 Sep 2025 10:00:00 +0000\r\n"
            "Subject: Verify now\r\n\r\nHello\r\n"
        )
        resp = self.client.post("/api/classify-email", json={"emailBody": "", "sender": "", "subject": "", "raw_eml": raw})
        pm = resp.json()["parsed_metadata"]
        self.assertIn("paypa1-verify.com", pm["from"])
        self.assertEqual(resp.status_code, 200)

    def test_authentication_extraction_and_alignment(self):
        res = self.analyze_phish()
        auth = res["authentication"]
        self.assertEqual(auth["spf"], "FAIL")
        self.assertEqual(auth["dmarc"], "FAIL")
        self.assertEqual(auth["dkim"], "NONE")
        self.assertIn("has_arc", auth)

    def test_received_chain_reconstructed(self):
        res = self.analyze_phish()
        hops = res["relay_hops"]
        self.assertEqual(len(hops), 3)
        positions = [h["position"] for h in hops]
        self.assertEqual(positions, sorted(positions))

    def test_forged_field_detection(self):
        res = self.analyze_phish()
        descs = " ".join(f["description"].lower() for f in res["indicators"])
        self.assertIn("reply-to domain mismatch", descs)
        self.assertIn("return-path domain", descs)

    def test_arc_extraction_when_present(self):
        from services.email_forensics_pipeline import parse_authentication_results
        hdrs = PHISH_HEADERS + [{"name": "ARC-Authentication-Results",
                                 "value": "i=1; mx.forwarder.com; spf=pass; dkim=pass; dmarc=pass"}]
        auth = parse_authentication_results(hdrs, "paypa1-verify.com")
        self.assertTrue(auth["has_arc"])
        self.assertIsNotNone(auth["arc_results"])


# ===========================================================================
# 3. Origin traceability
# ===========================================================================
class TestOriginTraceability(ForensicTestBase):
    def test_origin_trace_and_public_private_classification(self):
        res = self.analyze_phish()
        ips = {h["from_ip"]: h["is_public"] for h in res["relay_hops"] if h.get("from_ip")}
        # private/internal IPs must be excluded
        self.assertFalse(ips.get("10.0.0.2", True))
        # documentation-range IPs (RFC 5737) are deliberately NOT treated as routable origin
        self.assertFalse(ips.get("198.51.100.22", True))
        # genuinely public relay IP is classified as public
        self.assertTrue(ips.get("93.184.216.34", False))
        self.assertIn("public_ips_detected", res["diagnostics"])
        self.assertIn("93.184.216.34", res["diagnostics"]["public_ips_detected"])

    def test_geolocation_honest_when_no_public_ip(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": "hello", "sender": "a@b.test",
            "headers": [{"name": "Received", "value": "from local (192.168.1.1) by gw (192.168.1.254)"}],
        })
        geo = resp.json().get("geolocation")
        if geo:
            self.assertNotEqual(geo.get("provider_state"), "AVAILABLE")
            self.assertIsNone(geo.get("latitude"))

# ===========================================================================
# 4 & 6. Infrastructure & threat intelligence (provider-dependent, honest)
# ===========================================================================
class TestInfrastructureAndThreatIntel(ForensicTestBase):
    def test_geolocation_provider_state_is_honest(self):
        res = self.analyze_phish()
        geo = res.get("geolocation")
        if geo:
            self.assertIn(geo["provider_state"], ("AVAILABLE", "UNAVAILABLE", "UNKNOWN"))
            self.assertIn("does not establish the physical location", geo.get("disclaimer", ""))

    def test_threat_intel_marks_unavailable_without_provider(self):
        saved = os.environ.pop("VIRUSTOTAL_API_KEY", None)
        try:
            res = self.analyze_phish()
            statuses = {ti["status"] for ti in res.get("threat_intel", [])}
            self.assertIn("Unavailable", statuses)
        finally:
            if saved:
                os.environ["VIRUSTOTAL_API_KEY"] = saved

    def test_ip_intelligence_fields_when_available(self):
        """Controlled real-shaped IPinfo response; verifies the full field contract."""
        class FakeResp:
            status_code = 200
            def json(self):
                return {"ip": "93.184.216.34", "city": "Brisbane", "region": "Queensland",
                        "country": "AU", "loc": "-27.4679,153.0281", "timezone": "Australia/Brisbane",
                        "org": "AS36459 GitHub, Inc.",
                        "company": {"type": "hosting"},
                        "privacy": {"vpn": False, "proxy": False, "tor": False, "relay": False, "hosting": True}}
        from unittest.mock import patch
        from services.intel_providers import IPGeolocationProvider
        with patch.dict(os.environ, {"IPINFO_TOKEN": "test-token-not-a-real-key"}):
            with patch("services.intel_providers.requests.get", return_value=FakeResp()):
                geo = IPGeolocationProvider.get_geolocation("93.184.216.34")
        self.assertEqual(geo["provider_state"], "AVAILABLE")
        self.assertEqual(geo["asn"], "AS36459")
        self.assertEqual(geo["isp"], "GitHub, Inc.")
        self.assertEqual(geo["is_hosting"], True)
        self.assertEqual(geo["latitude"], -27.4679)
        self.assertIn("disclaimer", geo)


# ===========================================================================
# 5. Domain intelligence
# ===========================================================================
class TestDomainIntelligence(ForensicTestBase):
    def test_dns_real_lookup_contract(self):
        from services.email_forensics_pipeline import query_domain_dns
        res = query_domain_dns("example.com")
        self.assertIn(res["status"], ("AVAILABLE", "UNAVAILABLE", "UNKNOWN"))
        for key in ("resolved_ips", "mx_hosts", "spf_record", "dmarc_record", "lookup_time"):
            self.assertIn(key, res)

    def test_rdap_contract_never_fabricated(self):
        from services.rdap_provider import query_domain_rdap
        res = query_domain_rdap("example.com")
        self.assertIn(res["status"], ("AVAILABLE", "UNAVAILABLE"))
        if res["status"] == "UNAVAILABLE":
            self.assertIn("reason", res)
        else:
            for key in ("registrar", "registration_date", "expiration_date", "nameservers", "source"):
                self.assertIn(key, res)
            self.assertEqual(res["source"], "RDAP (rdap.org)")

    def test_rdap_available_with_controlled_response(self):
        class FakeResp:
            status_code = 200
            def json(self):
                return {
                    "handle": "EXAMPLE-DOM",
                    "events": [{"eventAction": "registration", "eventDate": "1995-08-14T04:00:00Z"},
                               {"eventAction": "expiration", "eventDate": "2027-08-13T04:00:00Z"}],
                    "entities": [{"roles": ["registrar"], "vcardArray": ["vcard", [["fn", {}, "text", "IANA-RESERVED"]]]}],
                    "nameservers": [{"ldhName": "A.IANA-SERVERS.NET"}, {"ldhName": "B.IANA-SERVERS.NET"}],
                }
        from unittest.mock import patch
        with patch("services.rdap_provider.requests.get", return_value=FakeResp()):
            res = self.analyze_phish()
        whois = res["domain_whois"]
        self.assertEqual(whois["status"], "AVAILABLE")
        self.assertEqual(whois["registration_date"][:4], "1995")
        self.assertTrue(whois["nameservers"])

# ===========================================================================
# 7. Attribution support
# ===========================================================================
class TestAttributionSupport(ForensicTestBase):
    def test_attribution_structure_and_disclaimers(self):
        res = self.analyze_phish()
        att = res["attribution"]
        self.assertIn("probable_infrastructure_attribution", att)
        self.assertIn("attribution_confidence_level", att)
        self.assertIn("compromised_account_indicators", att)
        self.assertIn("spoofed_domain_indicators", att)
        self.assertIn("anonymized_infrastructure_indicators", att)
        self.assertIn("limitations", att)
        self.assertGreaterEqual(att["spoofed_domain_indicators"], 1)
        self.assertGreaterEqual(att["compromised_account_indicators"], 1)


# ===========================================================================
# 8. Graph correlation
# ===========================================================================
class TestGraphCorrelation(ForensicTestBase):
    def test_graph_is_data_driven(self):
        res = self.analyze_phish()
        g = res["graph"]
        self.assertTrue(g["summary"]["data_driven"])
        self.assertGreater(g["summary"]["node_count"], 0)
        self.assertGreater(g["summary"]["edge_count"], 0)
        types = set(g["summary"]["node_types"])
        self.assertIn("email", types)
        self.assertIn("sender", types)
        self.assertIn("domain", types)
        self.assertIn("url", types)

    def test_graph_edges_reference_existing_nodes(self):
        res = self.analyze_phish()
        ids = {n["id"] for n in res["graph"]["nodes"]}
        for e in res["graph"]["edges"]:
            self.assertIn(e["source"], ids)
            self.assertIn(e["target"], ids)

    def test_graph_prior_incident_correlation(self):
        res = self.analyze_phish()
        self.case_store.create_case(res, analyst_id="tester")
        res2 = self.analyze_phish()
        self.assertIn("previous_incident", set(res2["graph"]["summary"]["node_types"]))

# ===========================================================================
# 13. Case management + 14. Evidence preservation / chain of custody
# ===========================================================================
class TestCaseManagement(ForensicTestBase):
    def test_create_search_update_case(self):
        res = self.analyze_phish()
        resp = self.client.post("/api/email/cases", json={"analysis": res, "analyst_id": "analyst-1"})
        self.assertEqual(resp.status_code, 200)
        case = resp.json()
        self.assertTrue(case["case_id"].startswith("CASE-"))
        self.assertIn(case["severity"], ("low", "medium", "high", "critical"))

        lst = self.client.get("/api/email/cases", params={"q": "paypa1"}).json()
        self.assertTrue(any(c["case_id"] == case["case_id"] for c in lst))

        upd = self.client.patch(f"/api/email/cases/{case['case_id']}", json={
            "status": "in_progress", "note": "Confirmed phishing kit pattern.",
            "analyst_id": "analyst-1"})
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(upd.json()["status"], "in_progress")
        self.assertTrue(upd.json()["notes"])

    def test_case_evidence_chain_of_custody(self):
        res = self.analyze_phish()
        case = self.case_store.create_case(res, analyst_id="analyst-1")
        self.assertTrue(case["evidence"])
        for ev in case["evidence"]:
            self.assertIn("evidence_id", ev)
            self.assertEqual(len(ev["sha256"]), 64)
            self.assertIn("collected_at", ev)
        self.assertTrue(case["analysis_metadata"]["metadata_hash"])
        fetched = self.case_store.get_case(case["case_id"])
        self.assertTrue(fetched["integrity"]["intact"])

    def test_integrity_detects_tampering(self):
        res = self.analyze_phish()
        case = self.case_store.create_case(res, analyst_id="analyst-1")
        with open(self.case_store._STORE_PATH, "r", encoding="utf-8") as f:
            cases = json.load(f)
        for c in cases:
            if c["case_id"] == case["case_id"]:
                c["risk_score"] = 0  # simulated post-collection modification
        with open(self.case_store._STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(cases, f)
        fetched = self.case_store.get_case(case["case_id"])
        self.assertFalse(fetched["integrity"]["intact"])


# ===========================================================================
# 15. Privacy / compliance
# ===========================================================================
class TestPrivacyCompliance(ForensicTestBase):
    def test_sensitive_data_masking(self):
        text = "Contact john.doe@example.com or call +1 555 019 2847, card 4111 1111 1111 1111."
        masked = self.privacy.mask_sensitive_text(text)
        self.assertNotIn("john.doe@example.com", masked)
        self.assertNotIn("4111 1111", masked)
        self.assertIn("****-****-****-1111", masked)
        self.assertIn("***", masked)

    def test_minimized_storage_no_raw_body(self):
        res = self.analyze_phish()
        case = self.case_store.create_case(res, analyst_id="tester")
        self.assertIsNone(case.get("raw_eml"))
        self.assertLessEqual(len(case.get("body_snippet") or ""), 300)

    def test_privacy_config_endpoints(self):
        cfg = self.client.get("/api/privacy/config").json()
        self.assertIn("retention_days", cfg)
        upd = self.client.put("/api/privacy/config", json={"retention_days": 30, "_analyst_id": "admin"})
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(upd.json()["retention_days"], 30)

    def test_authorized_access_control(self):
        self.privacy.save_config({"authorized_access_required": True, "authorized_analysts": ["analyst-1"]})
        resp = self.client.post("/api/email/cases", json={"analysis": self.analyze_safe(), "analyst_id": "intruder"})
        self.assertEqual(resp.status_code, 403)
        ok = self.client.post("/api/email/cases", json={"analysis": self.analyze_safe(), "analyst_id": "analyst-1"})
        self.assertEqual(ok.status_code, 200)
        self.privacy.save_config({"authorized_access_required": True, "authorized_analysts": []})

    def test_audit_log_records_actions(self):
        self.privacy.log_audit_event("test_action", {"x": 1}, analyst_id="tester")
        log = self.privacy.read_audit_log()
        self.assertTrue(any(e["action"] == "test_action" for e in log))

# ===========================================================================
# 16. Forensic reporting
# ===========================================================================
class TestForensicReporting(ForensicTestBase):
    def test_report_separates_evidence_inference_confidence_limitations(self):
        res = self.analyze_phish()
        case = self.case_store.create_case(res, analyst_id="analyst-1")
        resp = self.client.post("/api/email/report", json={"case_id": case["case_id"], "analyst_id": "analyst-1"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        report = body["report"]
        self.assertIn("observed_evidence", report)
        self.assertIn("analytical_inference", report)
        self.assertIn("unavailable_intelligence", report)
        self.assertIn("limitations", report)
        self.assertIn("report_metadata", report)
        for section in ("observed_evidence", "analytical_inference", "unavailable_intelligence"):
            for f_ in report[section]:
                self.assertIn("confidence", f_)
        self.assertIn("[LIMITATIONS]", body["report_text"])
        self.assertIn("does not prove a person's physical location", body["report_text"])

    def test_report_requires_input(self):
        resp = self.client.post("/api/email/report", json={})
        self.assertEqual(resp.status_code, 400)


# ===========================================================================
# 10. Real-time pipeline (auto-triage) + 12. Dashboard exposure
# ===========================================================================
class TestRealtimePipeline(ForensicTestBase):
    def test_auto_triage_high_risk_creates_alert_and_case(self):
        resp = self.client.post("/api/email/auto-triage", json={
            "uid": "user-1", "messageId": "gmail-msg-001",
            "sender": "security@paypa1-verify.com",
            "subject": "URGENT: Account suspended - verify immediately",
            "body": PHISH_BODY, "headers": PHISH_HEADERS})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["high_risk"])
        self.assertIsNotNone(data["case_id"])
        self.assertTrue(data["alert"]["requires_investigation"])

        alerts = self.client.get("/api/email/alerts").json()
        self.assertTrue(any(a["case_id"] == data["case_id"] for a in alerts))

    def test_auto_triage_low_risk_no_case(self):
        resp = self.client.post("/api/email/auto-triage", json={
            "uid": "user-1", "messageId": "gmail-msg-002",
            "sender": "no-reply@github.com", "subject": "Weekly digest",
            "body": SAFE_BODY, "headers": SAFE_HEADERS})
        data = resp.json()
        self.assertFalse(data["high_risk"])
        self.assertIsNone(data["case_id"])

    def test_dashboard_payload_exposes_all_sections(self):
        res = self.analyze_phish()
        for key in ("safety", "score", "confidence", "indicators", "authentication", "relay_hops",
                    "geolocation", "urls_forensics", "domain_dns", "domain_whois",
                    "attachments_forensics", "risk_factors", "campaign_correlations",
                    "threat_intel", "attribution", "graph", "evidence_metadata", "diagnostics"):
            self.assertIn(key, res, f"dashboard field missing: {key}")


# ===========================================================================
# 17. Attachment forensics
# ===========================================================================
class TestAttachmentForensics(ForensicTestBase):
    def test_double_extension_and_hashes(self):
        import hashlib
        resp = self.client.post("/api/classify-email", json={
            "emailBody": "See attached invoice.", "sender": "billing@evil.co",
            "subject": "Invoice", "headers": [],
            "attachments": [{"filename": "invoice.pdf.exe", "size_bytes": 999999,
                             "mime_type": "application/pdf",
                             "hash": hashlib.sha256(b"malware").hexdigest()}]})
        res = resp.json()
        descs = " ".join(f["description"].lower() for f in res["indicators"])
        self.assertIn("double extension", descs)
        self.assertTrue(res["attachments_forensics"])
        self.assertEqual(res["attachments_forensics"][0]["hash"][:8], hashlib.sha256(b"malware").hexdigest()[:8])


# ===========================================================================
# Regression coverage requested in final audit pass
# ===========================================================================
class TestFinalAuditRegressions(ForensicTestBase):
    def test_reply_to_same_domain_mailbox_divergence_not_domain_mismatch(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": "Routine support message.",
            "sender": "security@example.net",
            "subject": "Support",
            "headers": [
                {"name": "From", "value": "security@example.net"},
                {"name": "Reply-To", "value": "support@example.net"},
            ],
            "attachments": [],
        })
        res = resp.json()
        descs = "\n".join(f["description"] for f in res["indicators"])
        self.assertIn("Reply-To Mailbox Divergence", descs)
        self.assertNotIn("Reply-To Domain Mismatch", descs)
        risk_names = [f["factor"] for f in res["risk_factors"]]
        self.assertIn("Reply-To same-domain mailbox divergence", risk_names)
        self.assertNotIn("Reply-To domain mismatch", risk_names)

    def test_reply_to_different_domain_gets_domain_mismatch_penalty(self):
        resp = self.client.post("/api/classify-email", json={
            "emailBody": "Please review attached payment details.",
            "sender": "security@example.net",
            "subject": "Payment details",
            "headers": [
                {"name": "From", "value": "security@example.net"},
                {"name": "Reply-To", "value": "support@other.net"},
            ],
            "attachments": [],
        })
        res = resp.json()
        descs = "\n".join(f["description"] for f in res["indicators"])
        self.assertIn("Reply-To Domain Mismatch", descs)
        self.assertIn("Reply-To domain mismatch", [f["factor"] for f in res["risk_factors"]])

    def test_ip_classification_standards(self):
        from services.intel_providers import classify_ip_address, is_publicly_routable_ip
        cases = {
            "10.1.2.3": "rfc1918_private",
            "172.16.5.5": "rfc1918_private",
            "192.168.1.1": "rfc1918_private",
            "192.0.2.25": "documentation_test_net",
            "198.51.100.42": "documentation_test_net",
            "203.0.113.25": "documentation_test_net",
            "127.0.0.1": "loopback",
            "169.254.10.20": "link_local",
            "224.0.0.1": "multicast",
            "2001:db8::1": "documentation_test_net",
            "fc00::1": "ipv6_ula",
            "fe80::1": "link_local",
            "::1": "loopback",
            "ff02::1": "multicast",
        }
        for ip, expected in cases.items():
            with self.subTest(ip=ip):
                cls = classify_ip_address(ip)
                self.assertTrue(cls["valid"])
                self.assertEqual(cls["category"], expected)
                self.assertFalse(cls["usable_origin_evidence"])
                self.assertFalse(is_publicly_routable_ip(ip))
        self.assertEqual(classify_ip_address("999.1.1.1")["category"], "invalid")

    def test_origin_trace_rejects_only_documentation_addresses(self):
        from services.email_forensics_pipeline import analyze_origin_trace
        hops, origin = analyze_origin_trace([
            "from relay.example (203.0.113.25) by mx.example; Fri, 12 Sep 2025 10:00:00 +0000",
            "from client.example (198.51.100.42) by relay.example; Fri, 12 Sep 2025 09:59:00 +0000",
        ])
        self.assertIsNone(origin)
        self.assertTrue(all(h["ip_classification"]["category"] == "documentation_test_net" for h in hops))
        self.assertIn("cannot be used as real-world origin evidence", hops[0]["origin_candidate_reason"])

    def test_origin_trace_selects_earliest_reliable_public_node(self):
        from services.email_forensics_pipeline import analyze_origin_trace
        hops, origin = analyze_origin_trace([
            "from private (10.0.0.5) by mx.example; Fri, 12 Sep 2025 10:01:00 +0000",
            "from doc (203.0.113.25) by private; Fri, 12 Sep 2025 10:00:30 +0000",
            "from public (93.184.216.34) by doc; Fri, 12 Sep 2025 10:00:00 +0000",
        ])
        self.assertIsNotNone(origin)
        self.assertEqual(origin["from_ip"], "93.184.216.34")
        self.assertIn("observable mail infrastructure only", origin["origin_selection_explanation"])

    def test_rdap_403_distinguishes_configured_query_failed_unavailable(self):
        from unittest.mock import patch
        from services.rdap_provider import query_domain_rdap
        class Resp:
            status_code = 403
        with patch("services.rdap_provider.requests.get", return_value=Resp()):
            rdap = query_domain_rdap("example.net")
        self.assertEqual(rdap["provider_state"], "CONFIGURED")
        self.assertEqual(rdap["query_state"], "FAILED")
        self.assertEqual(rdap["result_state"], "UNAVAILABLE")
        self.assertIn("HTTP 403", rdap["reason"])
        self.assertNotIn("registrar", rdap)

    def test_provider_unavailable_vs_query_success_contract(self):
        from unittest.mock import patch
        from services.intel_providers import ThreatIntelligenceProvider, IPGeolocationProvider
        with patch.dict(os.environ, {}, clear=True):
            status, stats = ThreatIntelligenceProvider.check_ip("93.184.216.34")
        self.assertEqual(status, "Unavailable")
        self.assertEqual(stats["provider_state"], "NOT CONFIGURED")
        self.assertEqual(stats["query_state"], "NOT_RUN")
        self.assertEqual(stats["result_state"], "UNAVAILABLE")
        with patch.dict(os.environ, {"IPINFO_TOKEN": "token"}):
            geo = IPGeolocationProvider.get_geolocation("203.0.113.25")
        self.assertEqual(geo["query_state"], "NOT_RUN")
        self.assertEqual(geo["result_state"], "UNAVAILABLE")
        self.assertEqual(geo["ip_classification"]["category"], "documentation_test_net")

    def test_authentication_pass_does_not_override_malicious_content(self):
        headers = [
            {"name": "From", "value": "CEO <ceo@example.com>"},
            {"name": "Authentication-Results", "value": "mx; spf=pass smtp.mailfrom=example.com; dkim=pass header.d=example.com; dmarc=pass"},
        ]
        body = "URGENT wire transfer required. Change bank account details and send password verification at http://93.184.216.34/login"
        resp = self.client.post("/api/classify-email", json={"emailBody": body, "sender": "ceo@example.com", "subject": "URGENT wire transfer", "headers": headers, "attachments": []})
        res = resp.json()
        self.assertGreaterEqual(res["score"], 50)
        self.assertIn(res["safety"], ["suspicious", "dangerous"])
        descs = " ".join(f["description"] for f in res["indicators"])
        self.assertTrue("Payment Diversion" in descs or "Wire Transfer Diversion" in descs)

    def test_url_count_consistency_and_malformed_ip_rejection(self):
        body = "Visit https://example.com/a and https://example.com/a then http://999.1.1.1/b"
        resp = self.client.post("/api/classify-email", json={"emailBody": body, "sender": "user@example.com", "subject": "links", "headers": [], "attachments": []})
        res = resp.json()
        self.assertEqual(res["diagnostics"]["num_urls"], len(res["urls_forensics"]))
        self.assertEqual(res["diagnostics"]["num_urls"], 2)
        bad = [u for u in res["urls_forensics"] if u["hostname"] == "999.1.1.1"][0]
        self.assertFalse(bad["is_ip"])

    def test_report_contains_correlation_and_chain_of_custody(self):
        analysis = self.analyze_phish()
        case = self.client.post("/api/email/cases", json={"analysis": analysis, "analyst_id": "system"}).json()
        case = self.client.get(f"/api/email/cases/{case['case_id']}").json()
        report = self.client.post("/api/email/report", json={"case_id": case["case_id"], "analysis": analysis, "analyst_id": "system"}).json()["report"]
        self.assertIn("correlation_graph", report)
        self.assertIn("chain_of_custody", report)
        self.assertIn("evidence", case)
        self.assertTrue(case["integrity"]["metadata_hash_valid"])


if __name__ == "__main__":
    unittest.main()





