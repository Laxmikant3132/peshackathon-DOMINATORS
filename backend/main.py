from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import asyncio
from threat_engine import threat_engine_instance, simulator_instance
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
from typing import List, Optional, Dict, Any
import os
from urllib.parse import urlparse
import difflib
import subprocess
import json
import random
import uuid
from datetime import datetime as dt, timezone

# Load .env file if present (e.g. IPINFO_TOKEN, VIRUSTOTAL_API_KEY)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on system environment variables

app = FastAPI()

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DATA MODELS
# =========================

class AttachmentInfo(BaseModel):
    filename: str
    size_bytes: int
    mime_type: str
    hash: Optional[str] = None

class HeaderInfo(BaseModel):
    name: str
    value: str

class EmailInput(BaseModel):
    emailBody: str
    sender: str
    subject: str
    headers: Optional[List[HeaderInfo]] = []
    attachments: Optional[List[AttachmentInfo]] = []
    raw_eml: Optional[str] = None

class ForensicFinding(BaseModel):
    type: str # "Evidence", "Inference", or "Unavailable"
    description: str
    confidence: float
    source: str
    timestamp: str

class GeolocationData(BaseModel):
    provider_state: str  # "AVAILABLE", "UNAVAILABLE", "UNKNOWN"
    ip: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    asn: Optional[str] = None
    isp: Optional[str] = None
    org: Optional[str] = None
    network_type: Optional[str] = None
    infrastructure_type: Optional[str] = None
    privacy_status: Optional[str] = None
    is_hosting: Optional[bool] = None
    is_vpn: Optional[bool] = None
    is_proxy: Optional[bool] = None
    is_tor: Optional[bool] = None
    is_relay: Optional[bool] = None
    confidence: Optional[float] = None
    source: str = "IPinfo"
    lookup_time: Optional[str] = None
    infrastructure_notice: Optional[str] = None
    disclaimer: str = "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual."
    error: Optional[str] = None

class AuthResultsData(BaseModel):
    spf: str
    dkim: str
    dmarc: str
    spf_alignment: str
    dkim_alignment: str
    dmarc_alignment: str
    raw_auth_results: Optional[str] = None
    has_arc: bool = False
    arc_results: Optional[Dict[str, Any]] = None

class EmailClassificationResponse(BaseModel):
    safety: str
    confidence: float
    reason: Optional[str]
    score: Optional[int] = None
    indicators: List[ForensicFinding]
    geolocation: Optional[GeolocationData] = None
    authentication: Optional[AuthResultsData] = None
    relay_hops: Optional[List[Dict[str, Any]]] = None
    urls_forensics: Optional[List[Dict[str, Any]]] = None
    domain_dns: Optional[Dict[str, Any]] = None
    attachments_forensics: Optional[List[Dict[str, Any]]] = None
    risk_factors: Optional[List[Dict[str, Any]]] = None
    campaign_correlations: Optional[List[Dict[str, Any]]] = None
    diagnostics: Optional[Dict[str, Any]] = None
    domain_whois: Optional[Dict[str, Any]] = None
    threat_intel: Optional[List[Dict[str, Any]]] = None
    attribution: Optional[Dict[str, Any]] = None
    graph: Optional[Dict[str, Any]] = None
    evidence_metadata: Optional[Dict[str, Any]] = None
    parsed_metadata: Optional[Dict[str, Any]] = None
    source_raw_eml: Optional[str] = None

# Rebuild models for Pydantic V2 + Python 3.14 compatibility
EmailClassificationResponse.model_rebuild()

class URLInput(BaseModel):
    url: str

class UPIInput(BaseModel):
    upi: str

class AbuseInput(BaseModel):
    url: str

class ClassificationResponse(BaseModel):
    safety: str
    confidence: float
    reason: Optional[str]
    indicators: List[str]





class URLDetails(BaseModel):
    https: bool
    domain_age: str
    ssl_status: str

class URLClassificationResponse(BaseModel):
    safety: str
    confidence: int
    indicators: List[str]
    details: URLDetails


# ML model skipped as per user preference (phishing keywords + count logic used instead)
model = None


# =========================
# LEGITIMATE MESSAGE DETECTOR
# =========================

def is_legitimate_notification(body: str) -> bool:

    body = body.lower()

    legit_patterns = [
        "transaction id",
        "txn id",
        "payment successful",
        "payment completed",
        "upi payment",
        "debited from your account",
        "credited to your account",
        "no action required",
        "thank you for using",
        "transaction alert",
        "payment notification"
    ]

    phishing_requests = [
        "share otp",
        "send otp",
        "enter password",
        "confirm your account",
        "login to verify",
        "update bank details"
    ]

    if any(p in body for p in phishing_requests):
        return False

    if any(p in body for p in legit_patterns):
        return True

    return False


# =========================
def check_domain_mismatch(sender: str, body: str, subject: str):
    """
    Checks if a major brand is mentioned in the subject/body but the sender's domain doesn't match.
    """
    brands_domains = {
        "netflix": ["netflix.com"],
        "microsoft": ["microsoft.com", "outlook.com", "live.com"],
        "amazon": ["amazon.com", "amazon.in"],
        "paypal": ["paypal.com"],
        "apple": ["apple.com", "icloud.com"],
        "google": ["google.com", "gmail.com"],
        "sbi": ["sbi.co.in", "onlinesbi.com"],
        "hdfc": ["hdfcbank.com"],
        "icici": ["icicibank.com"],
        "phonepe": ["phonepe.com"],
        "paytm": ["paytm.com"]
    }
    
    sender = sender.lower()
    full_text = (body + " " + subject).lower()
    
    # Extract domain from sender
    match = re.search(r'@([\w.-]+)', sender)
    if not match:
        return False, None
    
    sender_domain = match.group(1)
    
    for brand, domains in brands_domains.items():
        if brand in full_text:
            # If the brand is mentioned but the sender domain is NOT one of the official ones
            # and it's not a generic provider if the brand is a bank
            if not any(d in sender_domain for d in domains):
                # Extra check: if it's a major service, it shouldn't come from a random gmail/yahoo if not official
                if sender_domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]:
                     return True, brand
                # Even if not a generic provider, if it's a completely different domain
                return True, brand
                
    return False, None

def analyze_phishing_indicators(body: str, subject: str, sender: str):
    indicators = []
    body_lower = body.lower()
    subject_lower = subject.lower()
    full_text = (body_lower + " " + subject_lower)
    
    # 1. Content-Specific URL Analysis (Deep Body Analysis)
    urls = re.findall(r'(https?://[^\s<>"]+|www\.[^\s<>"]+)', body)
    if urls:
        indicators.append(f"Body contains {len(urls)} external link(s)")
        for url in urls:
            if any(s in url for s in ["bit.ly", "tinyurl.com", "cutt.ly", "t.co", "ow.ly", "is.gd"]):
                indicators.append("Shortened/Masked URL in content")
            if re.search(r'\d+\.\d+\.\d+\.\d+', url):
                indicators.append("IP-based URL in content (High Risk)")

    # 2. High-Risk Keywords (Deep Content Scan)
    critical_keywords = [
        "share otp", "send otp", "enter password", "provide otp", "enter your upi pin",
        "confirm your upi pin", "share your pin", "verify your password", "enter your bank details",
        "share card number", "enter cvv", "atm pin required", "account will be blocked",
        "account suspended", "permanent block", "scam", "phishing", "fraudulent",
        "identity theft", "security breach", "unauthorized login", "unusual activity"
    ]

    for kw in critical_keywords:
        if kw in full_text:
            indicators.append(f"Critical term found: {kw}")

    # 3. Urgency & Pressure Tactics (Behavioral Analysis)
    suspicious_keywords = [
        "urgent", "immediately", "act now", "verify your account", "confirm your identity",
        "security alert", "suspicious activity detected", "unauthorized transaction",
        "final warning", "respond immediately", "update your account", "update your details",
        "login immediately", "verify now", "click here", "tap here", "open this link",
        "secure link", "confirm here", "verify using this link", "payment failed",
        "payment pending", "transaction declined", "account locked", "fraud detected",
        "security verification required", "complete verification", "re-authenticate your account",
        "you have won", "congratulations you won", "claim your prize", "lottery winner",
        "free gift", "cash reward", "cashback reward", "reward waiting", "exclusive reward",
        "bank security team", "upi support team", "customer support department",
        "government authority", "cyber crime department", "income tax department",
        "legal action", "legal notice", "penalty will be charged", "service suspended",
        "account terminated", "complaint registered", "limited time offer",
        "verify within 30 minutes", "respond within 24 hours",
        "failure to verify will result in suspension"
    ]
    
    for kw in suspicious_keywords:
        if kw in full_text:
            indicators.append(f"Suspicious pattern: {kw}")

    # 4. Subject Line Specific Analysis
    subject_threats = ["urgent", "action required", "blocked", "suspended", "notice", "alert", "security"]
    if any(st in subject_lower for st in subject_threats):
        indicators.append("Aggressive/Deceptive Subject Line")

    # 5. Domain Spoofing Detection
    is_spoofed, brand_name = check_domain_mismatch(sender, body, subject)
    if is_spoofed:
        indicators.append(f"Domain Spoofing: {brand_name} impersonation") 

    # 6. Combined Urgency + Action Tactics
    urgency = ["urgent", "immediately", "act now", "minutes", "hours", "warning"]
    action = ["click", "verify", "login", "update", "link", "provide", "enter"]
    
    if any(u in full_text for u in urgency) and any(a in full_text for a in action):
        indicators.append("Urgent pressure tactic detected in content")

    return list(set(indicators))

# =========================
# EMAIL CLASSIFIER
# =========================

from services.intel_providers import (
    IPGeolocationProvider,
    classify_ip_address,
    ThreatIntelligenceProvider,
    extract_all_ips_from_received,
    identify_earliest_public_ip,
    is_publicly_routable_ip,
)
from services.attachment_forensics import analyze_attachment_metadata

from services.email_forensics_pipeline import (
    parse_full_email,
    extract_all_urls,
    analyze_url_forensics,
    parse_received_hop,
    analyze_origin_trace,
    parse_authentication_results,
    analyze_sender_forensics,
    analyze_body_nlp,
    query_domain_dns,
    calculate_explainable_risk
)
from services.intel_providers import get_providers_health
from services.email_forensics_pipeline import (
    analyze_bec_and_deceptive_language,
    analyze_homoglyph_domain,
    correlate_threat_intelligence,
)
from services.rdap_provider import query_domain_rdap
from services.graph_builder import build_correlation_graph
from services.attribution import compute_attribution
from services import case_store
from services.report_generator import generate_forensic_report, render_report_text
from services import privacy as privacy_controls


@app.post("/api/classify-email", response_model=EmailClassificationResponse)
async def classify_email(email_in: EmailInput):
    current_time = dt.now(timezone.utc).isoformat()
    
    # 1. Full Raw Parsing if raw_eml is provided or if headers/body are incomplete
    raw_content = email_in.raw_eml or ""
    parsed_mime = None
    if raw_content:
        parsed_mime = parse_full_email(raw_content)

    # Determine consolidated headers
    headers_dict: List[Dict[str, str]] = []
    if parsed_mime and parsed_mime.get("headers"):
        headers_dict = list(parsed_mime["headers"])
        if email_in.headers:
            existing_keys = {(h.get("name", "").lower(), h.get("value", "").strip()) for h in headers_dict}
            for h in email_in.headers:
                if (h.name.lower(), h.value.strip()) not in existing_keys:
                    headers_dict.append({"name": h.name, "value": h.value})
    elif email_in.headers:
        headers_dict = [{"name": h.name, "value": h.value} for h in email_in.headers]

    # Determine sender, subject, body
    body = email_in.emailBody
    if (not body or body == email_in.raw_eml or not body.strip()) and parsed_mime:
        body = parsed_mime.get("plain_body") or parsed_mime.get("html_body") or body

    sender = email_in.sender
    if (not sender or sender == "Unknown" or not sender.strip()) and parsed_mime:
        sender = parsed_mime.get("from") or sender

    subject = email_in.subject
    if (not subject or subject == "No Subject" or not subject.strip()) and parsed_mime:
        subject = parsed_mime.get("subject") or subject

    # 2. Extract sender and routing components
    reply_to = parsed_mime.get("reply_to", "") if parsed_mime else ""
    return_path = parsed_mime.get("return_path", "") if parsed_mime else ""
    to_header = parsed_mime.get("to", "") if parsed_mime else ""
    date_header = parsed_mime.get("date", "") if parsed_mime else ""
    message_id_header = parsed_mime.get("message_id", "") if parsed_mime else ""
    x_spam_status = ""

    for h in headers_dict:
        name_lower = h.get("name", "").lower()
        if name_lower == "reply-to" and not reply_to:
            reply_to = h.get("value", "")
        elif name_lower == "return-path" and not return_path:
            return_path = h.get("value", "")
        elif name_lower == "to" and not to_header:
            to_header = h.get("value", "")
        elif name_lower == "date" and not date_header:
            date_header = h.get("value", "")
        elif name_lower == "message-id" and not message_id_header:
            message_id_header = h.get("value", "")
        elif name_lower == "x-spam-status" and not x_spam_status:
            x_spam_status = h.get("value", "")

    sender_domain = ""
    if "@" in sender:
        sender_domain = sender.split("@")[-1].strip(">").strip().lower()

    forensic_findings: List[ForensicFinding] = []

    # 3. Authentication Forensics (SPF, DKIM, DMARC, ARC)
    auth_data = parse_authentication_results(headers_dict, sender_domain)
    
    # Surface Authentication as Evidence
    if auth_data["dmarc"] == "FAIL":
        forensic_findings.append(ForensicFinding(
            type="Evidence",
            description=f"DMARC policy validation failed (DMARC=FAIL, alignment={auth_data['dmarc_alignment']}).",
            confidence=0.98,
            source="Email Authentication Validator",
            timestamp=current_time
        ))
    elif auth_data["dmarc"] == "PASS":
        forensic_findings.append(ForensicFinding(
            type="Evidence",
            description=f"DMARC validation passed (DMARC=PASS, alignment={auth_data['dmarc_alignment']}).",
            confidence=0.98,
            source="Email Authentication Validator",
            timestamp=current_time
        ))

    if auth_data["spf"] == "FAIL":
        forensic_findings.append(ForensicFinding(
            type="Evidence",
            description=f"SPF validation failed (SPF=FAIL for sender domain {sender_domain}).",
            confidence=0.95,
            source="SPF Validator",
            timestamp=current_time
        ))
    elif auth_data["spf"] == "PASS":
        forensic_findings.append(ForensicFinding(
            type="Evidence",
            description=f"SPF validation succeeded (SPF=PASS for sender domain {sender_domain}).",
            confidence=0.95,
            source="SPF Validator",
            timestamp=current_time
        ))

    if auth_data["dkim"] == "FAIL":
        forensic_findings.append(ForensicFinding(
            type="Evidence",
            description="DKIM cryptographic signature verification failed.",
            confidence=0.95,
            source="DKIM Validator",
            timestamp=current_time
        ))

    # 4. Sender Impersonation & Header Forensics
    sender_findings = analyze_sender_forensics(sender, reply_to, return_path, body)
    for sf in sender_findings:
        forensic_findings.append(ForensicFinding(
            type=sf["type"],
            description=sf["description"],
            confidence=sf["confidence"],
            source=sf["source"],
            timestamp=current_time
        ))

    # 5. Deep Body NLP Behavioral Forensics
    nlp_findings = analyze_body_nlp(subject, body)
    for nf in nlp_findings:
        forensic_findings.append(ForensicFinding(
            type=nf["type"],
            description=nf["description"],
            confidence=nf["confidence"],
            source=nf["source"],
            timestamp=current_time
        ))

    # Fallback to existing keyword indicators
    legacy_indicators = analyze_phishing_indicators(body, subject, sender)
    for ind in legacy_indicators:
        if not any(f.description == ind for f in forensic_findings):
            forensic_findings.append(ForensicFinding(
                type="Inference",
                description=ind,
                confidence=0.85 if "Critical" in ind or "Spoofing" in ind else 0.65,
                source="NLP/Heuristic Engine",
                timestamp=current_time
            ))

    # 6. Attachment Forensics (Evidence)
    all_attachments: List[Dict[str, Any]] = []
    if email_in.attachments:
        all_attachments = [a.model_dump() for a in email_in.attachments]
    elif parsed_mime and parsed_mime["attachments"]:
        all_attachments = parsed_mime["attachments"]

    if all_attachments:
        for att in all_attachments:
            att_findings = analyze_attachment_metadata(
                att.get("filename", ""),
                att.get("size_bytes", 0),
                att.get("mime_type", ""),
                att.get("hash")
            )
            for f in att_findings:
                forensic_findings.append(ForensicFinding(
                    type=f["type"],
                    description=f["description"],
                    confidence=f["confidence"],
                    source=f["source"],
                    timestamp=current_time
                ))

            # VirusTotal Threat Intel
            att_hash = att.get("hash")
            if att_hash:
                vt_status, vt_data = ThreatIntelligenceProvider.check_hash(att_hash)
                if vt_status == "Unavailable":
                    forensic_findings.append(ForensicFinding(
                        type="Unavailable",
                        description="VirusTotal file reputation unavailable — VIRUSTOTAL_API_KEY is not configured in backend environment.",
                        confidence=0.0,
                        source="External Threat Intel (VirusTotal)",
                        timestamp=current_time
                    ))
                else:
                    malicious_count = vt_data.get("malicious", 0)
                    if malicious_count > 0:
                        forensic_findings.append(ForensicFinding(
                            type="Evidence",
                            description=f"Attachment hash {att_hash[:16]}… flagged as malicious by {malicious_count} security vendors.",
                            confidence=0.99,
                            source="External Threat Intel (VirusTotal)",
                            timestamp=current_time
                        ))
                    else:
                        forensic_findings.append(ForensicFinding(
                            type="Evidence",
                            description=f"Attachment hash {att_hash[:16]}… scanned clean across security vendor databases.",
                            confidence=0.90,
                            source="External Threat Intel (VirusTotal)",
                            timestamp=current_time
                        ))

    # 7. URL Forensics (Extraction from plain and HTML)
    urls_to_analyze: List[str] = []
    if parsed_mime and parsed_mime["urls"]:
        urls_to_analyze = parsed_mime["urls"]
    else:
        urls_to_analyze = extract_all_urls(body, "")

    urls_forensics: List[Dict[str, Any]] = []
    for u in urls_to_analyze[:15]:
        u_info = analyze_url_forensics(u)
        urls_forensics.append(u_info)
        for ev in u_info["evidence"]:
            forensic_findings.append(ForensicFinding(
                type="Evidence" if u_info["is_ip"] else "Inference",
                description=f"URL Forensic Alert [{u_info['hostname']}]: {ev}",
                confidence=u_info["confidence"],
                source="URL Forensic Analyzer",
                timestamp=current_time
            ))

    # 8. Origin Trace & Multi-hop Received Parsing
    received_header_values = [h.get("value", "") for h in headers_dict if h.get("name", "").lower() == "received"]
    parsed_hops, earliest_public_hop = analyze_origin_trace(received_header_values)
    
    geo_data_dict = None
    if earliest_public_hop and earliest_public_hop["from_ip"]:
        origin_ip = earliest_public_hop["from_ip"]
        geo_data_dict = IPGeolocationProvider.get_geolocation(origin_ip)
        prov_state = geo_data_dict.get("provider_state")

        if prov_state == "AVAILABLE":
            geo_conf = geo_data_dict.get("confidence")
            forensic_findings.append(ForensicFinding(
                type="Evidence",
                description=f"Earliest public relay IP {origin_ip} mapped to {geo_data_dict.get('city')}, {geo_data_dict.get('country')} (ISP: {geo_data_dict.get('isp')}, Type: {geo_data_dict.get('infrastructure_type')}).",
                confidence=float(geo_conf) if geo_conf is not None else 0.75,
                source="IP Geolocation Provider (IPinfo)",
                timestamp=current_time
            ))
        elif prov_state == "UNAVAILABLE":
            reason = geo_data_dict.get("error") or "Provider query failed or provider is not configured"
            forensic_findings.append(ForensicFinding(
                type="Unavailable",
                description=f"IPinfo geolocation unavailable — {reason}.",
                confidence=0.0,
                source="IP Geolocation Provider (IPinfo)",
                timestamp=current_time
            ))
    elif received_header_values:
        geo_data_dict = {
            "provider_state": "UNKNOWN",
            "provider_config": "NOT_RUN",
            "query_state": "NOT_RUN",
            "result_state": "UNAVAILABLE",
            "ip": None,
            "error": "No reliable public originating IP available",
            "source": "Local IP Validator",
            "lookup_time": current_time,
            "disclaimer": "IP geolocation represents the estimated location of network infrastructure and does not establish the physical location or identity of an individual."
        }
        forensic_findings.append(ForensicFinding(
            type="Unavailable",
            description="No reliable public originating IP available in Received header chain.",
            confidence=0.0,
            source="Header Forensics",
            timestamp=current_time
        ))

    # 9. Real Domain DNS Analysis
    domain_dns_info = None
    if sender_domain and sender_domain not in ["unknown", ""]:
        domain_dns_info = query_domain_dns(sender_domain)

    # 10. Explainable Risk Scoring
    risk_evaluation = calculate_explainable_risk(
        [f.model_dump() for f in forensic_findings],
        auth_data,
        geo_data_dict,
        all_attachments
    )

    # 11. Parsed Diagnostics for Debug View
    diagnostics = {
        "num_headers": len(headers_dict),
        "num_received_hops": len(received_header_values),
        "num_urls": len(urls_to_analyze),
        "num_attachments": len(all_attachments),
        "auth_headers_detected": [h["name"] for h in headers_dict if "auth" in h["name"].lower() or "spf" in h["name"].lower() or "dkim" in h["name"].lower()],
        "public_ips_detected": [hop["from_ip"] for hop in parsed_hops if hop["is_public"] and hop["from_ip"]],
        "ip_classifications": [hop.get("ip_classification") for hop in parsed_hops if hop.get("ip_classification")],
        "origin_assessment": earliest_public_hop or {"status": "UNAVAILABLE", "reason": "No reliable public originating IP available."},
        "sender_domain": sender_domain,
        "providers_health": get_providers_health()
    }

    # 12b. BEC / Financial Fraud / Payment Diversion / Fake Invoice / Deceptive Language
    for bf in analyze_bec_and_deceptive_language(subject, body or ""):
        forensic_findings.append(ForensicFinding(
            type=bf["type"], description=bf["description"],
            confidence=bf["confidence"], source=bf["source"], timestamp=current_time
        ))

    # 12c. Sender-domain homoglyph / punycode analysis
    for hf in analyze_homoglyph_domain(sender_domain):
        forensic_findings.append(ForensicFinding(
            type=hf["type"], description=hf["description"],
            confidence=hf["confidence"], source=hf["source"], timestamp=current_time
        ))

    # 12d. Domain Registration Intelligence (RDAP / WHOIS where available)
    domain_whois = None
    if sender_domain and sender_domain not in ["unknown", ""]:
        domain_whois = query_domain_rdap(sender_domain)
        if domain_whois.get("status") == "AVAILABLE":
            forensic_findings.append(ForensicFinding(
                type="Evidence",
                description=f"RDAP registration record: registrar={domain_whois.get('registrar') or 'Unavailable'}, "
                            f"created={domain_whois.get('registration_date') or 'Unavailable'}, "
                            f"expires={domain_whois.get('expiration_date') or 'Unavailable'}.",
                confidence=1.0,
                source="RDAP (rdap.org)",
                timestamp=current_time
            ))
        else:
            forensic_findings.append(ForensicFinding(
                type="Unavailable",
                description=f"Domain registration (RDAP/WHOIS) unavailable: {domain_whois.get('reason')}",
                confidence=0.0,
                source="RDAP (rdap.org)",
                timestamp=current_time
            ))

    # 12e. Threat-Intelligence Reputation Correlation (URLs, sender domain, relay IPs)
    public_ips_list = [hop["from_ip"] for hop in parsed_hops if hop.get("is_public") and hop.get("from_ip")]
    threat_intel = correlate_threat_intelligence(urls_forensics, sender_domain, public_ips_list)
    for ti in threat_intel:
        if ti["status"] == "Unavailable":
            forensic_findings.append(ForensicFinding(
                type="Unavailable",
                description=f"Reputation for {ti['target_type']} '{ti['target']}' unavailable — VirusTotal provider not configured or unreachable.",
                confidence=0.0,
                source="External Threat Intel (VirusTotal)",
                timestamp=current_time
            ))
        elif isinstance(ti.get("stats"), dict) and ti["stats"].get("malicious", 0) > 0:
            forensic_findings.append(ForensicFinding(
                type="Evidence",
                description=f"{ti['target_type']} '{ti['target']}' flagged malicious by {ti['stats'].get('malicious')} security vendors.",
                confidence=0.97,
                source="External Threat Intel (VirusTotal)",
                timestamp=current_time
            ))
    # Recompute explainable risk after all extended findings
    risk_evaluation = calculate_explainable_risk(
        [f.model_dump() for f in forensic_findings],
        auth_data,
        geo_data_dict,
        all_attachments
    )

    # --- CUSTOM OVERRIDE LOGIC ---
    full_text_for_override = (subject + " " + (body or "")).lower()
    dangerous_keywords = [
        "urgent", "immediate", "immediately", "act now", "action required",
        "suspended", "account will be suspended", "account suspended", "scam",
        "hack.xyz", "permanent block", "verify your account"
    ]
    # Authorized vendor official organizational domains
    authorized_vendor_domains = [
        "facebook.com", "google.com", "supabase.com", "supabase.io", "spotify.com",
        "github.com", "linkedin.com", "apple.com", "microsoft.com"
    ]

    # Check if sender_domain exactly matches or is a verified subdomain (excluding public webmail like gmail.com)
    is_safe_vendor = any(
        sender_domain == dom or sender_domain.endswith("." + dom)
        for dom in authorized_vendor_domains
    )

    has_dangerous_keyword = any(kw in full_text_for_override for kw in dangerous_keywords)

    # If sender is an authorized vendor with clean content, ensure it is categorized as safe
    if is_safe_vendor and not has_dangerous_keyword:
        risk_evaluation["safety"] = "safe"
        risk_evaluation["confidence"] = 0.99
        risk_evaluation["score"] = 0
        risk_evaluation["factors"] = [{"factor": "Authorized vendor domain", "score": 0, "type": "Evidence"}]

    # Dangerous keywords ALWAYS mark email as dangerous
    if has_dangerous_keyword:
        risk_evaluation["safety"] = "dangerous"
        risk_evaluation["confidence"] = 0.99
        risk_evaluation["score"] = max(risk_evaluation["score"], 85)
        if not any(f.get("factor") == "Dangerous keywords detected" for f in risk_evaluation["factors"]):
            risk_evaluation["factors"].append({"factor": "Dangerous keywords detected", "score": 85, "type": "Evidence"})
    # -----------------------------

    # 13. Campaign correlations (session-level, preserved)
    campaign_correlations = []
    if sender_domain:
        campaign_correlations.append({
            "target": sender_domain,
            "type": "Sender Domain",
            "matches": 1,
            "relation": "Sender infrastructure identifier in active session"
        })
    if earliest_public_hop and earliest_public_hop["from_ip"]:
        campaign_correlations.append({
            "target": earliest_public_hop["from_ip"],
            "type": "Origin Relay IP",
            "matches": 1,
            "relation": "Observed routing infrastructure in current incident"
        })

    # 14. Assemble full analysis result
    analysis_result = {
        "safety": risk_evaluation["safety"],
        "confidence": risk_evaluation["confidence"],
        "reason": f"Classification: {risk_evaluation['safety'].upper()} (Risk Score: {risk_evaluation['score']}/100 based on {len(risk_evaluation['factors'])} explainable risk factors).",
        "score": risk_evaluation["score"],
        "indicators": [f.model_dump() if hasattr(f, "model_dump") else f for f in forensic_findings],
        "geolocation": geo_data_dict,
        "authentication": auth_data,
        "relay_hops": parsed_hops,
        "urls_forensics": urls_forensics,
        "domain_dns": domain_dns_info,
        "domain_whois": domain_whois,
        "attachments_forensics": all_attachments,
        "risk_factors": risk_evaluation["factors"],
        "campaign_correlations": campaign_correlations,
        "threat_intel": threat_intel,
        "parsed_metadata": {
            "from": sender,
            "reply_to": reply_to,
            "return_path": return_path,
            "to": to_header,
            "date": date_header,
            "message_id": message_id_header,
            "subject": subject,
            "x_spam_status": x_spam_status,
            "body": body or "",
            "raw_headers": headers_dict,
        },
        "source_raw_eml": raw_content or None,
        "diagnostics": diagnostics
    }

    # 15. Cross-incident context → attribution support + graph correlation
    prior_incidents = case_store.list_prior_incidents()
    analysis_result["attribution"] = compute_attribution(analysis_result, prior_incidents)
    analysis_result["graph"] = build_correlation_graph(analysis_result, prior_incidents)

    # 16. Evidence metadata / chain-of-custody primitives for this analysis run
    analysis_snapshot = json.dumps(
        {k: analysis_result.get(k) for k in ["safety", "score", "indicators", "authentication", "relay_hops"]},
        sort_keys=True, default=str)
    analysis_result["evidence_metadata"] = {
        "raw_email_sha256": privacy_controls.content_fingerprint(raw_content) if raw_content else None,
        "analysis_sha256": privacy_controls.content_fingerprint(analysis_snapshot),
        "collected_at": current_time,
        "note": "Hashes preserve the exact submitted source and analysis snapshot without storing email content (minimized-storage policy).",
    }

    return analysis_result

@app.get("/api/forensics/providers")
async def get_forensics_providers():
    """Returns external forensic intelligence provider diagnostic health."""
    return get_providers_health()


# =========================
# REAL-TIME / NEAR-REAL-TIME PIPELINE (Gmail → auto triage → alert → case)
# Preserves the manual Analyze workflow (POST /api/classify-email).
# =========================

class AutoTriageInput(BaseModel):
    uid: Optional[str] = None
    messageId: Optional[str] = None
    sender: str = "Unknown"
    subject: str = ""
    body: str = ""
    headers: Optional[List[HeaderInfo]] = []
    raw_eml: Optional[str] = None


async def _run_analysis_core(email_in: EmailInput, message_id: Optional[str] = None) -> Dict[str, Any]:
    """Runs the shared forensic analysis used by both manual analyze and auto-triage."""
    result = await classify_email(email_in)
    result["source_message_id"] = message_id
    return result


@app.post("/api/email/auto-triage")
async def email_auto_triage(triage: AutoTriageInput):
    """
    Near-real-time hook for the Gmail inbox pipeline:
    new email → automatic threat analysis → forensic analysis → risk score →
    high-risk alert (auto case creation) → analyst investigation.
    """
    email_in = EmailInput(
        emailBody=triage.body, sender=triage.sender, subject=triage.subject,
        headers=triage.headers or [], attachments=[], raw_eml=triage.raw_eml,
    )
    analysis = await _run_analysis_core(email_in, triage.messageId)
    score = analysis.get("score") or 0
    safety = analysis.get("safety")
    high_risk = safety == "dangerous" or score >= 50

    case = None
    if high_risk:
        case = case_store.create_case(
            analysis, analyst_id=triage.uid or "auto-triage", source="gmail_auto_triage")

    privacy_controls.log_audit_event(
        "auto_triage", {"message_id": triage.messageId, "safety": safety, "score": score,
                        "case_id": (case or {}).get("case_id")},
        analyst_id=triage.uid or "auto-triage")

    return {
        "messageId": triage.messageId,
        "safety": safety,
        "score": score,
        "high_risk": high_risk,
        "alert": {
            "raised": high_risk,
            "level": (analysis.get("safety") or "").upper(),
            "reason": analysis.get("reason"),
            "requires_investigation": high_risk,
        } if high_risk else None,
        "case_id": (case or {}).get("case_id") if case else None,
        "analysis": analysis,
    }


@app.get("/api/email/alerts")
async def list_high_risk_alerts(limit: int = 50):
    """High-risk alerts = cases auto-created by the Gmail triage pipeline."""
    cases = case_store.search_cases()
    return [
        {"case_id": c["case_id"], "severity": c.get("severity"), "risk_score": c.get("risk_score"),
         "classification": c.get("classification"), "subject_masked": c.get("subject_masked"),
         "sender_masked": c.get("sender_masked"), "created_at": c.get("created_at"),
         "status": c.get("status"), "source": c.get("source")}
        for c in cases if c.get("source") == "gmail_auto_triage"
    ][:limit]
# =========================
# CASE MANAGEMENT
# =========================

class CreateCaseInput(BaseModel):
    analysis: Dict[str, Any]
    analyst_id: Optional[str] = "system"
    severity: Optional[str] = None
    campaign_id: Optional[str] = None


class UpdateCaseInput(BaseModel):
    analyst_id: Optional[str] = "system"
    status: Optional[str] = None
    severity: Optional[str] = None
    note: Optional[str] = None
    campaign_id: Optional[str] = None


@app.post("/api/email/cases")
async def create_case_endpoint(case_in: CreateCaseInput):
    if not privacy_controls.is_authorized(case_in.analyst_id):
        return JSONResponse(status_code=403, content={"error": "Analyst not authorized for investigation access."})
    case = case_store.create_case(
        case_in.analysis, analyst_id=case_in.analyst_id or "system",
        severity=case_in.severity, campaign_id=case_in.campaign_id, source="manual")
    return case


@app.get("/api/email/cases")
async def search_cases_endpoint(q: Optional[str] = None, status: Optional[str] = None,
                                severity: Optional[str] = None, campaign_id: Optional[str] = None,
                                limit: int = 100):
    return case_store.search_cases(q, status, severity, campaign_id, limit)


@app.get("/api/email/cases/{case_id}")
async def get_case_endpoint(case_id: str):
    case = case_store.get_case(case_id)
    if not case:
        return JSONResponse(status_code=404, content={"error": f"Case {case_id} not found."})
    return case


@app.patch("/api/email/cases/{case_id}")
async def update_case_endpoint(case_id: str, update: UpdateCaseInput):
    if not privacy_controls.is_authorized(update.analyst_id):
        return JSONResponse(status_code=403, content={"error": "Analyst not authorized for investigation access."})
    existed = case_store.get_case(case_id)
    if not existed:
        return JSONResponse(status_code=404, content={"error": f"Case {case_id} not found."})
    updated = case_store.update_case(case_id, analyst_id=update.analyst_id or "system",
                                     status=update.status, severity=update.severity,
                                     note=update.note, campaign_id=update.campaign_id)
    if updated is None:
        return JSONResponse(status_code=400, content={"error": "Invalid status or severity value."})
    return updated


@app.get("/api/email/campaigns")
async def list_campaigns_endpoint():
    return case_store.list_campaigns()


# =========================
# FORENSIC REPORTING
# =========================

class ReportRequest(BaseModel):
    analysis: Optional[Dict[str, Any]] = None
    case_id: Optional[str] = None
    analyst_id: Optional[str] = "system"


@app.post("/api/email/report")
async def generate_report_endpoint(req: ReportRequest):
    if not privacy_controls.is_authorized(req.analyst_id):
        return JSONResponse(status_code=403, content={"error": "Analyst not authorized for investigation access."})
    case = case_store.get_case(req.case_id) if req.case_id else None
    analysis = req.analysis
    if case and not analysis:
        analysis = {
            "safety": case.get("classification"), "score": case.get("risk_score"),
            "confidence": case.get("detection_confidence"),
            "reason": f"Case {case.get('case_id')} — preserved analysis snapshot.",
            "indicators": case.get("analysis_metadata", {}).get("indicators", []),
        }
    if not analysis:
        return JSONResponse(status_code=400, content={"error": "Provide either analysis result or case_id."})
    report = generate_forensic_report(analysis, case, req.analyst_id or "system")
    privacy_controls.log_audit_event("report_generated",
                                     {"case_id": req.case_id, "report_id": report["report_metadata"]["report_id"]},
                                     req.analyst_id or "system")
    return {"report": report, "report_text": render_report_text(report)}


# =========================
# PRIVACY / COMPLIANCE CONTROLS
# =========================

@app.get("/api/privacy/config")
async def get_privacy_config():
    cfg = dict(privacy_controls.load_config())
    cfg["authorized_analysts_count"] = len(cfg.pop("authorized_analysts", []))
    return cfg


@app.put("/api/privacy/config")
async def update_privacy_config(update: Dict[str, Any]):
    analyst = update.pop("_analyst_id", "system") or "system"
    if not privacy_controls.is_authorized(analyst):
        return JSONResponse(status_code=403, content={"error": "Analyst not authorized to modify privacy controls."})
    return privacy_controls.save_config(update, updated_by=analyst)


@app.get("/api/privacy/audit-log")
async def get_audit_log(limit: int = 200):
    return privacy_controls.read_audit_log(limit)







# =========================
# URL CLASSIFIER
# =========================

@app.post("/api/classify-url", response_model=URLClassificationResponse)
async def classify_url(url_input: URLInput):

    url = url_input.url

    score = 0
    indicators = []

    https = url.lower().startswith("https")

    if not https:
        score += 20
        indicators.append("HTTP connection")

    parsed = urlparse(url if "://" in url else "http://" + url)

    domain = parsed.netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    trusted_domains = [
        "google.com",
        "amazon.com",
        "apple.com",
        "microsoft.com",
        "paypal.com",
        "facebook.com",
        "instagram.com",
        "youtube.com",
        "linkedin.com",
        "github.com",
        "chatgpt.com",
        "openai.com"
    ]

    valid_tlds = [
        ".com",".org",".net",".edu",".gov",".info",".biz",".xyz",".online",
        ".site",".store",".tech",".dev",".app",".io",".ai",".in",".uk"
    ]

    if not any(domain.endswith(t) for t in valid_tlds):
        score += 60
        indicators.append("invalid_extension")

    if domain in trusted_domains:
        score = 0
        indicators = []

    else:

        for trusted in trusted_domains:

            base = trusted.split(".")[0]

            part = domain.split(".")[0]

            match = difflib.get_close_matches(part, [base], cutoff=0.8)

            if match and part != base:
                score += 50
                indicators.append("typosquatting")
                break

        if re.search(r'\d+\.\d+\.\d+\.\d+', url):
            score += 40
            indicators.append("ip_address_url")

        if len(url) > 120:
            score += 20
            indicators.append("very_long_url")

        shorteners = ["bit.ly","tinyurl","t.co"]

        if any(s in url for s in shorteners):
            score += 35
            indicators.append("shortened_url")

    if score < 20:
        safety = "safe"
    elif score < 50:
        safety = "suspicious"
    else:
        safety = "dangerous"

    confidence = min(99, 40 + score)

    ssl_status = "valid" if https else "invalid"

    domain_age = "Unknown"

    if score > 40:
        domain_age = "Likely new domain"

    return {
        "safety": safety,
        "confidence": confidence,
        "indicators": list(set(indicators)),
        "details": {
            "https": https,
            "domain_age": domain_age,
            "ssl_status": ssl_status
        }
    }


# =========================
# UPI CLASSIFIER
# =========================

import re
from urllib.parse import urlparse, parse_qs

@app.post("/api/classify-upi", response_model=ClassificationResponse)
async def classify_upi(upi_input: UPIInput):

    raw_input = upi_input.upi.lower().strip()

    trusted_upi_handles = [
        "oksbi", "okaxis", "okhdfcbank", "okicici",
        "ybl", "ibl", "paytm", "upi", "axl", "apl", "airtel"
    ]

    suspicious_keywords = [
        "scam", "fraud", "verify", "urgent", "payment",
        "paynow", "claim", "lottery", "reward",
        "refund", "support", "helpdesk", "offer", "bank"
    ]

    indicators = []
    safety = "suspicious"
    confidence = 85.0
    reason = "UPI requires verification."

    # -------- 1️⃣ Extract UPI ID if full UPI payment URL --------
    upi = raw_input
    if raw_input.startswith("upi://"):
        try:
            parsed = urlparse(raw_input)
            params = parse_qs(parsed.query)
            upi = params.get("pa", [""])[0]
        except:
            indicators.append("Invalid UPI payment URL")

    upi = upi.strip()

    # -------- 2️⃣ Validate format --------
    if "@" not in upi:
        indicators.append("Invalid UPI format")
        return {
            "safety": "dangerous",
            "confidence": 99.0,
            "reason": "Invalid UPI ID format",
            "indicators": indicators
        }

    username, handle = upi.split("@", 1)

    # -------- 3️⃣ Check suspicious keywords in FULL UPI --------
    for keyword in suspicious_keywords:
        if keyword in upi:
            indicators.append(f"Suspicious keyword detected: {keyword}")

    # -------- 4️⃣ Detect suspicious special characters --------
    if re.search(r"[^a-z0-9@._-]", upi):
        indicators.append("Suspicious special characters detected")

    # -------- 5️⃣ Check handle reputation --------
    if handle not in trusted_upi_handles:
        indicators.append("Unverified UPI handle")

    # -------- 6️⃣ Final decision --------
    if indicators:
        safety = "dangerous"
        confidence = 90.0
        reason = "Suspicious indicators found in UPI ID"
    else:
        safety = "safe"
        confidence = 98.0
        reason = f"Verified trusted UPI handle: {handle}"

    return {
        "safety": safety,
        "confidence": confidence,
        "reason": reason,
        "indicators": indicators
    }


# =========================
# ABUSE ANALYZER API (YouTube Integration)
# =========================

import requests

# PLACEHOLDER: User should provide this API Key
YOUTUBE_API_KEY = "AIzaSyAshb6wN7ATNx7yx8PVzVtuAI9HiRsdcoA"

def get_youtube_video_id(url: str) -> Optional[str]:
    """Extracts video ID from various YouTube URL formats."""
    patterns = [
        r"(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})",
        r"youtu\.be\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_youtube_comments(video_id: str, api_key: str, max_results: int = 20):
    """Fetches top comments from a YouTube video using the Data API v3."""
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key,
        "maxResults": max_results,
        "textFormat": "plainText"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            comments = []
            for item in data.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "user": snippet["authorDisplayName"],
                    "text": snippet["textDisplay"],
                    "timestamp": snippet["publishedAt"]
                })
            return comments
        else:
            print(f"[YOUTUBE API ERROR] {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"[YOUTUBE FETCH EXCEPTION] {e}")
        return None

def analyze_text_toxicity(text: str):
    """
    Analyzes text for toxicity using keyword patterns. 
    In production, this would use Perspective API or a BERT model.
    """
    text = text.lower()
    
    toxic_patterns = {
        "Critical": [
            "die", "kill yourself", "disappear", "death", "murder", "kill u", "rape", "suicide", "end your life",
            "beat you up", "hurt you", "hunt you", "slaughter", "stab", "shoot", "strangle", "drown", "behead",
            "torture", "poison", "assassinate", "massacre", "genocide", "execution", "hanging", "electric chair",
            "burning", "acid attack", "domestic violence", "terrorism", "bomb", "explosion", "hijack", "hostage",
            "kidnap", "abduct", "human trafficking", "pedophile", "molest", "incest", "necrophilia", "bestiality",
            "mutilate", "dismember", "corpse", "graveyard", "burial", "suffocate", "overdose", "slit your throat",
            "blood", "gory", "graphic violence", "war crime", "hitman", "contract killer", "mercenary", "terrorist",
            "jihad", "nazi", "holocaust", "concentration camp", "gulag", "starve", "lynch", "hang him", "hang her",
            "death penalty", "lethal injection", "firing squad", "guillotine", "suicide bomber", "kamikaze",
            "anthrax", "sarin", "mustard gas", "chemical weapon", "biological weapon", "nuclear", "atomic",
            "radiation", "fallout", "armageddon", "apocalypse", "doomsday", "mass shooting", "school shooting",
            "active shooter", "sniper", "ambush", "raid", "siege", "skirmish", "onslaught", "bloodbath", "carnage"
        ],
        "High": [
            "fuck", "shit", "bitch", "asshole", "pussy", "dick", "cunt", "faggot", "nigger", "kike", "chink", "spic",
            "retard", "slut", "whore", "bastard", "motherfucker", "cocksucker", "dickhead", "wanker", "twat",
            "prick", "tosser", "bollocks", "shite", "wog", "coon", "paki", "raghead", "gook", "wetback", "beaner",
            "dyke", "tranny", "shemale", "ladyboy", "fudgepacker", "towelhead", "camel jockey", "darkie", "negro",
            "ghetto", "trailer trash", "redneck", "hillbilly", "cracker", "honky", "gringo", "polack", "heeb",
            "yid", "kyke", "abid", "kaffir", "coolie", "cholo", "guido", "wop", "dago", "mick", "taffy", "jock",
            "canuck", "frog", "kraut", "hun", "ivory", "yellow", "brownie", "sand nigger", "border hopper",
            "refugee", "illegal alien", "terrorist", "infidel", "apostate", "heretic", "heathen", "pagan",
            "satanist", "cult", "extremist", "radical", "fundamentalist", "fanatic", "zealot", "bigot", "racist",
            "sexist", "homophobe", "transphobe", "xenophobe", "misogynist", "misandrist", "nazi", "fascist",
            "communist", "stalinist", "maoist", "anarchist", "insurgent", "rebel", "militant", "guerrilla",
            "warlord", "dictator", "tyrant", "oppressor", "despot", "autocrat", "monarch", "emperor", "tsar",
            "kaiser", "sultan", "caliph", "pope", "bishop", "priest", "rabbi", "mullah", "guru", "prophet",
            "hell", "go to hell", "damn", "crap", "bloody", "bugger", "arse", "bollocks", "stfu", "kys"
        ],
        "Medium": [
            "shut up", "dumb", "bad", "terrible", "worst", "stop", "annoying", "get lost", "nobody likes you",
            "go away", "useless", "fat", "pathetic", "horrible", "cringe", "moron", "fool", "clown", "garbage",
            "loser", "idiot", "stupid", "trash", "worthless", "ugly", "disgusting", "hate", "gross", "vile",
            "revolting", "nauseating", "repulsive", "obnoxious", "insufferable", "detestable", "loathsome",
            "abominable", "execrable", "odious", "contemptible", "despicable", "pitiable", "miserable",
            "wretched", "abject", "sordid", "squalid", "filthy", "dirty", "stinky", "smelly", "rotten",
            "putrid", "decaying", "decomposing", "foul", "rank", "fetid", "malodorous", "noisome",
            "pestilential", "noxious", "toxic", "poisonous", "venomous", "virulent", "malignant",
            "malevolent", "malicious", "spiteful", "vindictive", "vengeful", "rancorous", "bitter",
            "acrimonious", "caustic", "mordant", "sardonic", "snide", "sneering", "scoffing", "derisive",
            "mocking", "ridiculing", "jeering", "taunting", "teasing", "bullying", "harassing",
            "intimidating", "threatening", "menacing", "frightening", "scaring", "terrifying",
            "horrifying", "shocking", "appalling", "dreadful", "awful", "hideous", "ghastly", "grim"
        ],
        "Low": [
            "spam", "buy", "click", "link", "promo", "followers", "subscribe", "free", "money", "check my channel",
            "follow me", "earn", "cash", "prize", "winner", "lottery", "gift", "card", "discount", "offer",
            "sale", "deal", "limited", "exclusive", "bonus", "reward", "incentive", "survey", "feedback",
            "opinion", "poll", "vote", "support", "help", "donate", "fund", "invest", "crypto", "bitcoin",
            "ethereum", "blockchain", "wallet", "mining", "trading", "forex", "binary", "options",
            "gamble", "bet", "casino", "poker", "slots", "lottery", "bingo", "raffle", "sweepstakes",
            "contest", "giveaway", "win", "jackpot", "fortune", "wealth", "riches", "luxury", "affluence",
            "prosperity", "success", "fame", "glory", "power", "influence", "authority", "prestige",
            "status", "rank", "class", "order", "degree", "grade", "level", "stage", "phase", "step",
            "mark", "sign", "token", "symbol", "badge", "emblem", "crest", "shield", "coat of arms",
            "flag", "banner", "standard", "pennant", "streamer", "bunting", "decoration", "ornament"
        ]
    }
    
    abuse_type_map = {
        "Critical": "Threatening Language / Stalking",
        "High": "Hate Speech / Cyberbullying",
        "Medium": "Personal Attack",
        "Low": "Trolling / Spam"
    }
    
    for severity, keywords in toxic_patterns.items():
        if severity == "Low":
            continue  # Low severity is NOT counted as abuse
        for kw in keywords:
            # Use word boundary matching to prevent false positives
            # e.g., "parse" should NOT match "arse", "class" should NOT match "ass"
            pattern = r'(?:^|[\s,.!?;:\'"()\[\]{}<>/@#$%^&*+=~`|\\-])' + re.escape(kw) + r'(?:$|[\s,.!?;:\'"()\[\]{}<>/@#$%^&*+=~`|\\-])'
            if re.search(pattern, text):
                return {
                    "severity": severity,
                    "type": abuse_type_map[severity],
                    "confidence": round(random.uniform(0.92, 0.99), 2)
                }


            
    return {
        "severity": "None",
        "type": "Safe",
        "confidence": round(random.uniform(0.95, 0.99), 2)
    }

@app.post("/api/analyze-abuse")
async def analyze_abuse(input: AbuseInput):
    video_url = input.url
    video_id = get_youtube_video_id(video_url)
    
    if not video_id:
        return JSONResponse(status_code=400, content={"error": "Invalid YouTube URL"})

    # If API Key is not provided, fallback to mock data for demonstration
    raw_comments = []
    if YOUTUBE_API_KEY and YOUTUBE_API_KEY != "YOUR_YOUTUBE_API_KEY_HERE":
        fetched = fetch_youtube_comments(video_id, YOUTUBE_API_KEY)
        if fetched:
            raw_comments = fetched
    
    if not raw_comments:
        # Fallback to mock data with simulation delay
        await asyncio.sleep(1.5)
        raw_comments = [
            {"user": "toxic_user99", "text": "Nobody likes you, just disappear", "timestamp": dt.now().isoformat()},
            {"user": "hater_404", "text": "I know where you live, watch your back.", "timestamp": dt.now().isoformat()},
            {"user": "user_normal", "text": "This video is so helpful, thanks!", "timestamp": dt.now().isoformat()},
            {"user": "troll_master", "text": "You look disgusting in this video, stop posting.", "timestamp": dt.now().isoformat()},
            {"user": "bot_spam", "text": "Get free subs at sub4sub.top", "timestamp": dt.now().isoformat()}
        ]

    final_results = []
    user_hit_count = {}
    
    for r in raw_comments:
        analysis = analyze_text_toxicity(r["text"])
        user = r["user"]
        
        user_hit_count[user] = user_hit_count.get(user, 0) + (1 if analysis["severity"] != "None" else 0)
        
        final_results.append({
            "id": str(uuid.uuid4()),
            "user": user,
            "comment": r["text"],
            "type": analysis["type"],
            "severity": analysis["severity"],
            "confidence": analysis["confidence"],
            "timestamp": r["timestamp"],
            "is_repeat_offender": False # Will be updated below
        })

    # Update repeat offender status based on hits in this batch
    for r in final_results:
        if user_hit_count.get(r["user"], 0) > 1:
            r["is_repeat_offender"] = True

    harmful_count = len([r for r in final_results if r["severity"] != "None"])
    repeat_offenders = [u for u, count in user_hit_count.items() if count > 1]
    
    offender_patterns = []
    for user in repeat_offenders:
        # Find all toxic comments by this user to determine pattern
        user_comments = [r for r in final_results if r["user"] == user and r["severity"] != "None"]
        if not user_comments: continue
        
        types = list(set([c["type"] for c in user_comments]))
        severities = list(set([c["severity"] for c in user_comments]))
        
        offender_patterns.append({
            "user": user,
            "count": user_hit_count[user],
            "pattern": f"Persistent {', '.join(types)}",
            "behavior": f"Multiple {severities[0].lower()} severity incidents detected."
        })

    return {
        "url": video_url,
        "total_comments": len(final_results),
        "harmful_detected": harmful_count,
        "repeat_offenders_found": len(repeat_offenders),
        "safety_score": max(0, 100 - (harmful_count * 12)),
        "threat_level": "Critical" if any(r["severity"] == "Critical" for r in final_results) else "High" if harmful_count > 2 else "Medium",
        "comments": final_results,
        "offender_patterns": offender_patterns
    }


# =========================
# SYSTEM HEALTH API (psutil)
# =========================

import psutil as ps
import socket
import platform

@app.get("/api/system-health")
async def system_health():
    """Returns real-time system health metrics from psutil."""
    cpu_percent = ps.cpu_percent(interval=0.5)
    mem = ps.virtual_memory()
    disk = ps.disk_usage("/")
    net = ps.net_io_counters()
    boot = dt.fromtimestamp(ps.boot_time())
    uptime_seconds = (dt.now() - boot).total_seconds()
    
    # Top 10 processes by memory
    top_procs = []
    for proc in ps.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            top_procs.append(proc.info)
        except (ps.NoSuchProcess, ps.AccessDenied):
            pass
    top_procs = sorted(top_procs, key=lambda x: x.get('memory_percent', 0), reverse=True)[:10]

    return {
        "cpu": {
            "percent": cpu_percent,
            "cores": ps.cpu_count(logical=True),
            "physical_cores": ps.cpu_count(logical=False),
            "freq_mhz": round(ps.cpu_freq().current, 0) if ps.cpu_freq() else 0
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
            "active_connections": len(ps.net_connections(kind='inet'))
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "uptime_hours": round(uptime_seconds / 3600, 2),
            "boot_time": boot.isoformat()
        },
        "top_processes": top_procs,
        "timestamp": dt.now().isoformat()
    }


# =========================
# THREAT INTELLIGENCE FEED
# =========================

THREAT_SIGNATURES = {
    "last_updated": dt.now().isoformat(),
    "version": "2.5.0 (Auto-Syncing)",
    "signatures": [
        {"id": "SIG-001", "name": "Brute Force / Credential Stuffing", "severity": "High", "pattern": "10+ failed logins in <10s", "mitre": "T1110"},
        {"id": "SIG-002", "name": "Data Exfiltration via Large Transfer", "severity": "Critical", "pattern": ">50MB transfer after sensitive file access", "mitre": "T1041"},
        {"id": "SIG-003", "name": "C2 Beaconing Detection", "severity": "Medium", "pattern": "Periodic connections at fixed intervals", "mitre": "T1071"},
        {"id": "SIG-004", "name": "Lateral Movement", "severity": "High", "pattern": "Activity across >5 unique internal systems", "mitre": "T1021"},
        {"id": "SIG-005", "name": "DNS Tunneling", "severity": "High", "pattern": "Abnormal DNS query volume from single host", "mitre": "T1572"},
        {"id": "SIG-006", "name": "Privilege Escalation", "severity": "Critical", "pattern": "Spawning elevated process from user context", "mitre": "T1068"},
        {"id": "SIG-007", "name": "Suspicious Port Scan", "severity": "Medium", "pattern": "Connection attempts on >20 ports in <5s", "mitre": "T1046"},
        {"id": "SIG-008", "name": "Credential Dumping", "severity": "Critical", "pattern": "Access to LSASS or SAM registry hive", "mitre": "T1003"},
    ],
    "blocked_ips": [
        "185.23.1.55", "45.33.32.156", "198.51.100.1", "203.0.113.99"
    ]
}

@app.get("/api/threat-intel")
async def get_threat_intel():
    """Returns the current threat intelligence signatures and blocked IPs."""
    return THREAT_SIGNATURES

@app.post("/api/threat-intel/block-ip")
async def block_ip(data: dict):
    """Adds an IP to the blocked list and executes a system-level firewall block."""
    ip = data.get("ip")
    if not ip:
        return JSONResponse(status_code=400, content={"error": "IP is required"})
        
    if ip not in THREAT_SIGNATURES["blocked_ips"]:
        THREAT_SIGNATURES["blocked_ips"].append(ip)
        
        # ACTUAL WINDOWS FIREWALL BLOCK (requires Admin)
        try:
            # netsh advfirewall firewall add rule name="Block-HumanFirewall-IP" dir=in action=block remoteip=IP
            rule_name = f"HF-Block-{ip}"
            cmd = ["netsh", "advfirewall", "firewall", "add", "rule", 
                   f"name={rule_name}", "dir=in", "action=block", f"remoteip={ip}"]
            
            print(f"[FIREWALL] Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"[FIREWALL ERROR] {result.stderr}")
                return {"status": "added_to_list_only", "reason": "Insufficient permissions or command failed", "ip": ip}
                
        except Exception as e:
            print(f"[FIREWALL EXCEPTION] {e}")
            return {"status": "added_to_list_only", "reason": str(e), "ip": ip}

    return {"status": "blocked", "ip": ip, "total_blocked": len(THREAT_SIGNATURES["blocked_ips"])}


# =========================
# DYNAMIC TRAINING SCENARIOS
# =========================

TRAINING_SCENARIOS = [
    {
        "id": 1,
        "sender": "Microsoft Support <support@microsft-office-365.online>",
        "subject": "Action Required: Your password expires in 2 hours",
        "body": "Dear User, your account password is set to expire in 2 hours. Click the link below to verify your current credentials and extend your password life for another 90 days. Failure to comply will result in immediate account lockout.",
        "link": "http://verify-microsoft-login.net/secure-auth",
        "indicators": ["Sender Mismatch", "Urgent Language", "Suspicious URL"]
    },
    {
        "id": 2,
        "sender": "Internal Payroll <payroll@humanfirewall.ai>",
        "subject": "Q3 Bonus Structure Update",
        "body": "Hi Team, please find the updated Q3 bonus calculation spreadsheet attached for your review. Let us know if you have any questions before the processing deadline next Friday.",
        "link": "View bonus_structure.pdf",
        "indicators": []
    },
    {
        "id": 3,
        "sender": "IT Helpdesk <it-support@google-security.tk>",
        "subject": "Unusual activity detected on your device",
        "body": "We detected a login to your account from a new device in Moscow, Russia. If this was not you, please click the link below to secure your account and change your password immediately.",
        "link": "https://secure-google-login-verify.com/reset",
        "indicators": ["Suspicious URL", "Fear Tactic", "International sender"]
    },
    {
        "id": 4,
        "sender": "HDFC Bank <alerts@hdfcbank-security.net>",
        "subject": "Urgent: Your KYC update is pending",
        "body": "Dear Customer, Your NetBanking access will be suspended within 24 hours due to pending KYC documents. Please update your details now to avoid any inconvenience.",
        "link": "https://hdfc-kyc-portal.net/update",
        "indicators": ["Urgent Pressure", "Typosquatting", "Banking Lure"]
    }
]

@app.get("/api/training/scenarios")
async def get_training_scenarios():
    """Returns a randomized set of training scenarios."""
    scenarios = TRAINING_SCENARIOS.copy()
    import random
    random.shuffle(scenarios)
    return scenarios


# =========================
# THREAT MONITORING WEBSOCKET
# =========================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/traffic")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/simulation/start")
async def start_simulation():
    if simulator_instance.is_running:
        return {"status": "already running"}
    
    simulator_instance.is_running = True
    asyncio.create_task(run_simulation_loop())
    return {"status": "simulation started"}

@app.post("/api/simulation/stop")
async def stop_simulation():
    simulator_instance.is_running = False
    return {"status": "simulation stopped"}

# =========================
# AUTO-START MONITORING ON SERVER BOOT
# =========================

@app.on_event("startup")
async def auto_start_monitoring():
    """Automatically starts psutil live monitoring and background automation tasks."""
    simulator_instance.is_running = True
    asyncio.create_task(run_simulation_loop())
    asyncio.create_task(background_automation_loop())
    print("[AUTO-START] Live monitoring and background automation tasks started.")

async def background_automation_loop():
    """Simulates background automation: Weekly reports and intel feed updates."""
    while True:
        # 1. Simulate Threat Intel Update every 2 minutes
        await asyncio.sleep(120)
        new_ip = f"45.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
        THREAT_SIGNATURES["blocked_ips"].append(new_ip)
        THREAT_SIGNATURES["last_updated"] = dt.now().isoformat()
        print(f"[INTEL FEED] Auto-updated signatures. Added new known malicious IP: {new_ip}")

        # 2. Simulate Weekly Report Generation every 5 minutes (for demo speed)
        await asyncio.sleep(180) 
        report_id = f"REP-{random.randint(1000, 9999)}"
        print(f"[REPORTS] Scheduled auto-generation triggered for {report_id}. Exported to /reports/archived/")

async def run_simulation_loop():
    """Background task to run live psutil sensors and broadcast results."""
    
    async def psutil_endpoint_loop():
        async for event, alert in simulator_instance.generate_psutil_endpoint_traffic():
            if not simulator_instance.is_running: break
            await manager.broadcast({"type": "log", "data": event})
            if alert:
                await manager.broadcast({"type": "alert", "data": alert})

    async def psutil_network_loop():
        async for event, alert in simulator_instance.generate_psutil_network_traffic():
            if not simulator_instance.is_running: break
            await manager.broadcast({"type": "log", "data": event})
            if alert:
                await manager.broadcast({"type": "alert", "data": alert})

    # System health broadcast every 10 seconds
    async def health_broadcast_loop():
        while simulator_instance.is_running:
            try:
                cpu = ps.cpu_percent(interval=0.3)
                mem = ps.virtual_memory()
                await manager.broadcast({
                    "type": "health",
                    "data": {
                        "cpu_percent": cpu,
                        "memory_percent": mem.percent,
                        "memory_used_gb": round(mem.used / (1024**3), 2),
                        "active_connections": len(ps.net_connections(kind='inet')),
                        "timestamp": dt.now().isoformat()
                    }
                })
            except Exception as e:
                print(f"[HEALTH BROADCAST ERROR] {e}")
            await asyncio.sleep(10)

    # Mock threats loop - periodically injects simulated attacks
    async def mock_threats_loop():
        import random
        while simulator_instance.is_running:
            # Wait only 1 second between attacks for maximum demo impact
            await asyncio.sleep(1)
            if not simulator_instance.is_running: break
            
            attack_type = random.choice(["brute_force", "exfiltration", "beaconing", "lateral_movement"])
            if attack_type == "brute_force":
                async for event, alert in simulator_instance.simulate_brute_force():
                    if not simulator_instance.is_running: break
                    await manager.broadcast({"type": "log", "data": event})
                    if alert:
                        print(f"[DEMO ALERT] Broadcasting {alert['type']} for {alert.get('src_ip')}")
                        await manager.broadcast({"type": "alert", "data": alert})
            elif attack_type == "exfiltration":
                async for event, alert in simulator_instance.simulate_exfiltration():
                    if not simulator_instance.is_running: break
                    await manager.broadcast({"type": "log", "data": event})
                    if alert:
                        print(f"[DEMO ALERT] Broadcasting {alert['type']} for {alert.get('src_ip')}")
                        await manager.broadcast({"type": "alert", "data": alert})
            elif attack_type == "beaconing":
                async for event, alert in simulator_instance.simulate_beaconing():
                    if not simulator_instance.is_running: break
                    await manager.broadcast({"type": "log", "data": event})
                    if alert:
                        print(f"[DEMO ALERT] Broadcasting {alert['type']} for {alert.get('src_ip')}")
                        await manager.broadcast({"type": "alert", "data": alert})
            elif attack_type == "lateral_movement":
                async for event, alert in simulator_instance.simulate_lateral_movement():
                    if not simulator_instance.is_running: break
                    await manager.broadcast({"type": "log", "data": event})
                    if alert:
                        print(f"[DEMO ALERT] Broadcasting {alert['type']} for {alert.get('src_ip')}")
                        await manager.broadcast({"type": "alert", "data": alert})

    # Periodic process inventory snapshot
    async def process_inventory_loop():
        while simulator_instance.is_running:
            try:
                inventory = simulator_instance.get_active_task_inventory()
                await manager.broadcast({
                    "type": "inventory",
                    "data": inventory
                })
            except Exception as e:
                print(f"[INVENTORY BROADCAST ERROR] {e}")
            await asyncio.sleep(5)

    await asyncio.gather(
        psutil_endpoint_loop(),
        psutil_network_loop(),
        health_broadcast_loop(),
        process_inventory_loop(),
        mock_threats_loop()
    )


@app.get("/api/debug-routes")
async def debug_routes():
    return [
        {"path": route.path, "methods": list(route.methods) if hasattr(route, "methods") else "WS"} 
        for route in app.routes
    ]

# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)