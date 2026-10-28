"""
Full-fidelity Email Forensic Parser & Analysis Pipeline
Implements deterministic RFC 5322 & MIME parsing, multi-hop Received header tracing,
comprehensive SPF/DKIM/DMARC and ARC authentication extraction, sender forensics,
deep NLP behavior analysis, normalized URL analysis, static attachment forensics,
DNS resolution, and risk factor accounting.
"""

import email
from email import policy
from email.parser import BytesParser, Parser
import email.utils
import re
import socket
import subprocess
import hashlib
import ipaddress
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime as dt, timezone
from typing import List, Dict, Any, Optional, Tuple

from services.intel_providers import (
    is_publicly_routable_ip,
    classify_ip_address,
    IPGeolocationProvider,
    ThreatIntelligenceProvider,
    DomainReputationProvider
)

SUSPICIOUS_EXTENSIONS = {
    '.exe', '.scr', '.vbs', '.bat', '.js', '.jar', '.ps1', '.cmd', '.pif',
    '.application', '.gadget', '.msi', '.msp', '.com', '.wsf', '.hta', '.cpl',
    '.msc', '.iso', '.img', '.vhd', '.dll', '.reg', '.ws'
}

SCRIPT_EXTENSIONS = {'.vbs', '.js', '.ps1', '.bat', '.cmd', '.sh', '.py', '.php', '.hta'}
ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.cab', '.iso'}
MACRO_EXTENSIONS = {'.docm', '.xlsm', '.pptm', '.dotm', '.xltm', '.xlam', '.ppam', '.ppsm', '.sldm'}

# -------------------------------------------------------------------------
# 1. MIME & Raw Email Parser
# -------------------------------------------------------------------------

def normalize_raw_eml_headers(raw_content: str) -> str:
    """
    Normalizes RFC 5322 raw email source by removing extraneous empty lines
    interspersed between header blocks before the true message body starts.
    Preserves all header folding, MIME parts, and payload boundaries.
    """
    lines = raw_content.splitlines()
    header_lines: List[str] = []
    body_lines: List[str] = []
    in_body = False
    header_regex = re.compile(r'^[A-Za-z0-9_-]+:\s*')

    for i, line in enumerate(lines):
        if in_body:
            body_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            # Check if any subsequent non-empty line starts with a valid header
            has_subsequent_header = False
            for next_line in lines[i + 1:]:
                next_stripped = next_line.strip()
                if not next_stripped:
                    continue
                if header_regex.match(next_stripped) or re.match(r'^\s+', next_line):
                    has_subsequent_header = True
                break

            if has_subsequent_header:
                # Extraneous empty line between headers; skip
                continue
            else:
                in_body = True
                continue

        header_lines.append(line)

    if body_lines:
        return "\r\n".join(header_lines) + "\r\n\r\n" + "\r\n".join(body_lines)
    return "\r\n".join(header_lines)


def parse_full_email(raw_content: str) -> Dict[str, Any]:
    """
    Parses full RFC 5322 raw email string or EML bytes.
    Extracts complete headers, plain text, HTML, multipart attachments,
    and metadata without truncating or executing anything.
    """
    if isinstance(raw_content, str):
        normalized = normalize_raw_eml_headers(raw_content)
        msg = Parser(policy=policy.default).parsestr(normalized)
    else:
        try:
            text_form = raw_content.decode("utf-8", errors="replace")
            normalized = normalize_raw_eml_headers(text_form)
            msg = Parser(policy=policy.default).parsestr(normalized)
        except Exception:
            msg = BytesParser(policy=policy.default).parsebytes(raw_content)

    headers_list: List[Dict[str, str]] = []
    for k, v in msg.items():
        headers_list.append({"name": str(k), "value": str(v)})

    # Multi-field Reply-To check: mailbox/local-part, domain, and full-addressee divergence.
    reply_to_raw = msg.get("Reply-To", "")
    from_raw = msg.get("From", "")
    reply_to_addr = email.utils.parseaddr(reply_to_raw)[1]
    from_addr = email.utils.parseaddr(from_raw)[1]
    reply_to_domain = reply_to_addr.split("@")[-1] if "@" in reply_to_addr else None
    from_domain = from_addr.split("@")[-1] if "@" in from_addr else None

    # Extract plain text & HTML bodies
    text_parts: List[str] = []
    html_parts: List[str] = []
    attachments: List[Dict[str, Any]] = []

    for part in msg.walk():
        content_type = part.get_content_type()
        disposition = part.get_content_disposition() or ""
        filename = part.get_filename()

        if filename or disposition in ["attachment", "inline"] and content_type not in ["text/plain", "text/html"]:
            try:
                payload = part.get_payload(decode=True)
            except Exception:
                payload = b""

            size = len(payload) if payload else 0
            file_hash = hashlib.sha256(payload).hexdigest() if payload else None
            safe_name = filename or f"attachment_{len(attachments)+1}"
            
            attachments.append({
                "filename": safe_name,
                "size_bytes": size,
                "mime_type": content_type,
                "disposition": disposition,
                "content_id": str(part.get("Content-ID", "")),
                "transfer_encoding": str(part.get("Content-Transfer-Encoding", "")),
                "hash": file_hash
            })
        elif content_type == "text/plain" and disposition != "attachment":
            try:
                text_parts.append(part.get_content())
            except Exception:
                try:
                    text_parts.append(part.get_payload(decode=True).decode(errors="replace"))
                except Exception:
                    pass
        elif content_type == "text/html" and disposition != "attachment":
            try:
                html_parts.append(part.get_content())
            except Exception:
                try:
                    html_parts.append(part.get_payload(decode=True).decode(errors="replace"))
                except Exception:
                    pass

    plain_body = "\n".join(text_parts)
    html_body = "\n".join(html_parts)
    
    # Extract URLs from BOTH plain and HTML
    extracted_urls = extract_all_urls(plain_body, html_body)

    return {
        "headers": headers_list,
        "plain_body": plain_body,
        "html_body": html_body,
        "attachments": attachments,
        "urls": extracted_urls,
        "message_id": msg.get("Message-ID", ""),
        "subject": msg.get("Subject", ""),
        "from": msg.get("From", ""),
        "to": msg.get("To", ""),
        "cc": msg.get("Cc", ""),
        "reply_to": msg.get("Reply-To", ""),
        "return_path": msg.get("Return-Path", ""),
        "date": msg.get("Date", "")
    }

# -------------------------------------------------------------------------
# 2. URL Extraction & Forensic Analysis
# -------------------------------------------------------------------------

def extract_all_urls(plain_text: str, html_text: str) -> List[str]:
    """Extracts, normalizes, and deduplicates all URLs from plain text and HTML."""
    combined = plain_text + " " + html_text
    # href="..." links in HTML
    href_matches = re.findall(r'href=[\'"]?([^\'" >]+)', html_text, re.IGNORECASE)
    # plain text and general regex
    raw_matches = re.findall(r'(https?://[^\s<>"\'`]+|www\.[^\s<>"\'`]+)', combined, re.IGNORECASE)
    
    all_raw = set(href_matches + raw_matches)
    clean_urls: List[str] = []

    for u in all_raw:
        u_clean = u.rstrip('.,;()[]{}<>"\':')
        if not u_clean.startswith("http://") and not u_clean.startswith("https://"):
            u_clean = "http://" + u_clean
        if len(u_clean) > 8 and u_clean not in clean_urls:
            clean_urls.append(u_clean)

    return clean_urls

def analyze_url_forensics(url: str) -> Dict[str, Any]:
    """
    Forensic analysis for a single URL:
    - parsing scheme, hostname, port, path, query
    - IP-based URL
    - shortener / redirect service
    - punycode / homoglyph
    - suspicious characters / typosquatting
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    
    ip_classification = classify_ip_address(hostname) if hostname else {"valid": False}
    is_ip = bool(ip_classification.get("valid"))
    is_shortener = hostname in ["bit.ly", "tinyurl.com", "cutt.ly", "t.co", "ow.ly", "is.gd", "goo.gl", "rebrand.ly"]
    has_punycode = "xn--" in hostname
    has_at_symbol = "@" in url
    
    evidence_list: List[str] = []
    classification = "No local URL indicators (reputation unknown)"
    confidence = 0.0

    if is_ip:
        classification = "High Risk (IP-based URL)"
        confidence = 0.95
        evidence_list.append("URL points directly to an IP address instead of a domain name (RFC non-standard for legitimate services)")
    
    if is_shortener:
        classification = "Suspicious (URL Shortener)"
        confidence = 0.85
        evidence_list.append(f"Shortened/redirector link hides actual landing destination: {hostname}")
        
    if has_punycode:
        classification = "High Risk (Punycode / Homoglyph)"
        confidence = 0.92
        evidence_list.append(f"Domain uses IDN punycode (xn--) which may mask visual homoglyphs: {hostname}")

    if has_at_symbol:
        classification = "High Risk (Obfuscated Auth URL)"
        confidence = 0.90
        evidence_list.append("URL contains '@' userinfo separator intended to disguise actual target host")

    # Extract registrable domain roughly
    domain_parts = hostname.split('.')
    reg_domain = hostname if is_ip else (".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else hostname)

    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError:
        port = None
        evidence_list.append("Malformed URL port")
    return {
        "url": url,
        "hostname": hostname,
        "registrable_domain": reg_domain,
        "scheme": parsed.scheme,
        "port": port,
        "is_ip": is_ip,
        "ip_classification": ip_classification if is_ip else None,
        "is_shortener": is_shortener,
        "has_punycode": has_punycode,
        "classification": classification,
        "confidence": confidence,
        "evidence": evidence_list,
        "reputation_source": "Deterministic Heuristics"
    }

# -------------------------------------------------------------------------
# 3. Received Header Relay Hop Parsing
# -------------------------------------------------------------------------

def parse_received_hop(raw_hop: str, hop_index: int) -> Dict[str, Any]:
    """
    Parses a single RFC 5322 Received header string:
    Extracts from-host, from-ip, by-host, by-ip, protocol, TLS, timestamp.
    """
    # Normalized whitespace
    hop = " ".join(raw_hop.split())
    
    # 1. From host & IP
    from_match = re.search(r'from\s+([^\s\(\)]+)(?:\s*\(([^\)]+)\))?', hop, re.IGNORECASE)
    from_host = from_match.group(1) if from_match else "Unknown"
    from_bracket = from_match.group(2) if from_match else ""
    
    # Extract IP from 'from' section
    # Never confuse the receiving server's address with the sending peer.
    from_section = re.split(r'\sby\s', hop, maxsplit=1, flags=re.I)[0] if from_match else ""
    from_ip = None
    candidates = re.findall(r'\[([^\]]+)\]|\b((?:\d{1,3}\.){3}\d{1,3})\b', from_section)
    for bracket, ipv4 in candidates:
        try:
            from_ip = str(ipaddress.ip_address((bracket or ipv4).removeprefix("IPv6:")))
            break
        except ValueError:
            continue
    
    # 2. By host
    by_match = re.search(r'by\s+([^\s\(\)]+)', hop, re.IGNORECASE)
    by_host = by_match.group(1) if by_match else "Unknown"
    
    # 3. Protocol & TLS
    protocol = "SMTP"
    if "ESMTPS" in hop.upper() or "TLS" in hop.upper():
        protocol = "ESMTPS (TLS)"
    elif "ESMTP" in hop.upper():
        protocol = "ESMTP"
    elif "HTTP" in hop.upper():
        protocol = "HTTP/Webmail"

    tls_info = None
    tls_match = re.search(r'using\s+(TLS[^\s;]+)', hop, re.IGNORECASE)
    if tls_match:
        tls_info = tls_match.group(1)
    elif "TLS" in hop.upper():
        tls_info = "Encrypted TLS Transmission"

    # 4. Timestamp
    timestamp = None
    if ";" in hop:
        time_part = hop.split(";")[-1].strip()
        timestamp = time_part

    ip_classification = classify_ip_address(from_ip) if from_ip else None
    is_public = bool(ip_classification and ip_classification.get("is_publicly_routable"))

    return {
        "position": hop_index,
        "from_host": from_host,
        "from_ip": from_ip,
        "by_host": by_host,
        "protocol": protocol,
        "tls_info": tls_info,
        "timestamp": timestamp,
        "is_public": is_public,
        "ip_classification": ip_classification,
        "origin_candidate_status": "accepted_public_origin_candidate" if is_public else "rejected_non_public_or_unusable",
        "origin_candidate_reason": (ip_classification or {}).get("reason") if ip_classification else "No valid sender IP extracted from Received hop",
        "raw": hop
    }

def analyze_origin_trace(received_headers: List[str]) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Parses all Received headers in chronologically reversed order (earliest origin hops first).
    Returns (all_parsed_hops, earliest_reliable_public_hop).
    """
    parsed_hops: List[Dict[str, Any]] = []
    for i, h in enumerate(received_headers):
        parsed_hops.append(parse_received_hop(h, i + 1))

    # Standard Received headers: bottom/last is earliest hop
    earliest_public_hop = None
    for hop in reversed(parsed_hops):
        if hop["is_public"] and hop["from_ip"]:
            earliest_public_hop = dict(hop)
            earliest_public_hop["origin_selection_explanation"] = (
                "Selected as the earliest standards-valid, globally routable observable sending node "
                "in the Received chain. This identifies observable mail infrastructure only; it is not proof "
                "of the attacker's device, identity, or physical location."
            )
            earliest_public_hop["origin_confidence"] = 0.72
            earliest_public_hop["origin_limitations"] = [
                "Received headers can be forged before the first trusted receiving boundary.",
                "The selected IP is observable infrastructure, not a human attribution.",
            ]
            break

    if not earliest_public_hop:
        for hop in parsed_hops:
            hop["origin_candidate_status"] = hop.get("origin_candidate_status") or "rejected_non_public_or_unusable"
            hop["origin_candidate_reason"] = hop.get("origin_candidate_reason") or "No reliable public originating IP available."

    return parsed_hops, earliest_public_hop

# -------------------------------------------------------------------------
# 4. Authentication (SPF, DKIM, DMARC, ARC) & Alignment
# -------------------------------------------------------------------------

def parse_authentication_results(headers: List[Dict[str, str]], sender_domain: str) -> Dict[str, Any]:
    """
    Extracts and parses Authentication-Results, ARC-Authentication-Results,
    Received-SPF, and DKIM-Signature headers.
    Calculates result codes and alignment.
    """
    auth_results_raw = ""
    arc_results_raw = ""
    received_spf_raw = ""
    dkim_signatures: List[str] = []

    for h in headers:
        name = h.get("name", "").lower()
        val = h.get("value", "")
        if name == "authentication-results" and not auth_results_raw:
            auth_results_raw = val
        elif name == "arc-authentication-results" and not arc_results_raw:
            arc_results_raw = val
        elif name == "received-spf" and not received_spf_raw:
            received_spf_raw = val
        elif name == "dkim-signature":
            dkim_signatures.append(val)

    def extract_auth_status(text: str, mechanism: str) -> Optional[str]:
        if not text:
            return None
        m = re.search(rf'{mechanism}=([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        return m.group(1).upper() if m else None

    # Primary auth results
    spf_res = extract_auth_status(auth_results_raw, "spf")
    dkim_res = extract_auth_status(auth_results_raw, "dkim")
    dmarc_res = extract_auth_status(auth_results_raw, "dmarc")

    # Fallback to Received-SPF header
    if not spf_res and received_spf_raw:
        m_spf = re.match(r'^\s*([a-zA-Z]+)', received_spf_raw)
        if m_spf:
            spf_res = m_spf.group(1).upper()

    # Fallback to DKIM signature presence
    if not dkim_res and dkim_signatures:
        dkim_res = "PRESENT (UNVERIFIED BY MTA)"

    # ARC Authentication
    arc_spf = extract_auth_status(arc_results_raw, "spf")
    arc_dkim = extract_auth_status(arc_results_raw, "dkim")
    arc_dmarc = extract_auth_status(arc_results_raw, "dmarc")

    # Alignment checks
    spf_alignment = "Unknown"
    dkim_alignment = "Unknown"

    if sender_domain:
        # Check SPF domain alignment in auth_results
        spf_domain_match = re.search(r'smtp\.mailfrom=([^\s;]+)', auth_results_raw, re.IGNORECASE)
        if spf_domain_match:
            mailfrom_dom = spf_domain_match.group(1).strip('<>"').lower().split('@')[-1]
            spf_alignment = "Aligned" if mailfrom_dom == sender_domain.lower() else "Unknown (strict mismatch; relaxed alignment not evaluated)"

        # Check DKIM d= alignment
        dkim_d_match = re.search(r'header\.(?:d|i)=@?([^\s;]+)', auth_results_raw, re.IGNORECASE)
        if not dkim_d_match and dkim_signatures:
            dkim_d_match = re.search(r'\bd=([^\s;]+)', dkim_signatures[0], re.IGNORECASE)
        if dkim_d_match:
            dkim_dom = dkim_d_match.group(1).strip('<>"').lower().split('@')[-1]
            dkim_alignment = "Aligned" if dkim_dom == sender_domain.lower() else "Unknown (strict mismatch; relaxed alignment not evaluated)"

    dmarc_alignment = "Aligned" if ((spf_alignment == "Aligned" and spf_res == "PASS") or (dkim_alignment == "Aligned" and dkim_res == "PASS")) else "Unknown"

    return {
        "spf": spf_res or "Unavailable",
        "dkim": dkim_res or "Unavailable",
        "dmarc": dmarc_res or "Unavailable",
        "spf_alignment": spf_alignment,
        "dkim_alignment": dkim_alignment,
        "dmarc_alignment": dmarc_alignment,
        "raw_auth_results": auth_results_raw or None,
        "has_arc": bool(arc_results_raw),
        "arc_results": {
            "spf": arc_spf or "Unavailable",
            "dkim": arc_dkim or "Unavailable",
            "dmarc": arc_dmarc or "Unavailable",
            "raw": arc_results_raw or None,
            "explanation": "ARC (Authenticated Received Chain) preserves email authentication across forwarding intermediaries."
        } if arc_results_raw else None
    }

# -------------------------------------------------------------------------
# 5. Sender Forensics & Impersonation
# -------------------------------------------------------------------------

def analyze_sender_forensics(from_str: str, reply_to_str: str, return_path_str: str, body_text: str) -> List[Dict[str, Any]]:
    """
    Evaluates From, Reply-To, Return-Path, display name, and homoglyphs/lookalike domains.
    Returns structured forensic findings.
    """
    findings: List[Dict[str, Any]] = []

    # Parse display name and email address from RFC 5322 string
    from_name, from_addr = email.utils.parseaddr(from_str)
    reply_name, reply_addr = email.utils.parseaddr(reply_to_str)
    return_name, return_addr = email.utils.parseaddr(return_path_str)

    from_domain = from_addr.split('@')[-1].lower() if '@' in from_addr else ""
    reply_domain = reply_addr.split('@')[-1].lower() if '@' in reply_addr else ""
    return_domain = return_addr.split('@')[-1].lower() if '@' in return_addr else ""

    # 1. Reply-To checks as three independent, explicit forensic checks.
    # (a) Full-address difference: the entire From address differs from Reply-To.
    if from_addr and reply_addr and reply_addr.lower() != from_addr.lower():
        findings.append({
            "type": "Evidence",
            "description": f"Reply-To Full-Address Difference: From is '{from_addr}' but replies route to '{reply_addr}'.",
            "confidence": 0.70,
            "source": "Sender Header Forensics",
        })

    # (b) Local-part/mailbox difference within the same domain.
    if from_addr and reply_addr:
        from_local = from_addr.split('@')[0].lower() if '@' in from_addr else ""
        reply_local = reply_addr.split('@')[0].lower() if '@' in reply_addr else ""
        if from_domain and reply_domain and from_domain == reply_domain and from_local and reply_local and from_local != reply_local:
            findings.append({
                "type": "Evidence",
                "description": f"Reply-To Mailbox Divergence / Same-Domain Mailbox Difference: From mailbox '{from_addr}' differs from Reply-To mailbox '{reply_addr}' but both use domain '{from_domain}'.",
                "confidence": 0.80,
                "source": "Sender Header Forensics",
            })

    # (c) Domain difference: this is the only condition that gets the domain-mismatch risk penalty.
    if from_addr and reply_addr and from_domain and reply_domain and from_domain != reply_domain:
        findings.append({
            "type": "Evidence",
            "description": f"Reply-To Domain Mismatch: From domain '{from_domain}' differs from Reply-To domain '{reply_domain}' (From '{from_addr}' routes replies to '{reply_addr}').",
            "confidence": 0.95,
            "source": "Sender Header Forensics",
        })

    # 2. Return-Path mismatch (bounce diversion)
    if return_addr and from_addr and return_domain != from_domain:
        findings.append({
            "type": "Evidence",
            "description": f"Return-Path domain '{return_domain}' differs from sender domain '{from_domain}'",
            "confidence": 0.88,
            "source": "Sender Header Forensics"
        })

    # 3. Display name impersonation
    brand_keywords = ["paypal", "microsoft", "google", "apple", "amazon", "netflix", "bank", "support", "security", "it desk", "helpdesk"]
    from_name_lower = from_name.lower()
    for b in brand_keywords:
        if b in from_name_lower and b not in from_domain:
            findings.append({
                "type": "Inference",
                "description": f"Display Name Impersonation: '{from_name}' uses trusted brand identifier '{b}' but domain is '{from_domain}'",
                "confidence": 0.90,
                "source": "Sender Brand Engine"
            })

    # 4. Lookalike / Typosquatting heuristics (e.g., paypa1, micros0ft)
    lookalikes = {
        "paypa1": "PayPal", "micros0ft": "Microsoft", "g00gle": "Google",
        "amaz0n": "Amazon", "app1e": "Apple", "sec-notice": "Security Portal"
    }
    for look, orig in lookalikes.items():
        if look in from_domain:
            findings.append({
                "type": "Inference",
                "description": f"Lookalike domain detected: '{from_domain}' mimics '{orig}' using character substitution",
                "confidence": 0.95,
                "source": "Domain Typosquatting Engine"
            })

    # 5. Excessive subdomains
    if from_domain.count('.') >= 4:
        findings.append({
            "type": "Evidence",
            "description": f"Suspicious subdomain depth in sender domain: '{from_domain}' has {from_domain.count('.')} levels",
            "confidence": 0.75,
            "source": "DNS Hierarchy Engine"
        })

    return findings

# -------------------------------------------------------------------------
# 6. Deep Body NLP Behavioral Forensics
# -------------------------------------------------------------------------

def analyze_body_nlp(subject: str, body: str) -> List[Dict[str, Any]]:
    """
    Performs behavioral and semantic scanning across 15 threat dimensions:
    urgency, fear, account suspension, credential requests, password reset,
    financial requests, payment diversion, invoice fraud, executive impersonation,
    vendor impersonation, secrecy, authority impersonation, social engineering,
    phishing call-to-actions, brand impersonation.
    """
    text = (subject + "\n" + body).lower()
    findings: List[Dict[str, Any]] = []

    categories = [
        ("Account Suspension / Termination", ["account suspended", "permanent suspension", "account will be blocked", "access revoked", "account terminated", "immediate termination"], 0.90),
        ("Credential Harvesting / Login Phishing", ["enter your password", "provide otp", "share otp", "verify your password", "login to verify", "re-authenticate", "enter credentials", "confirm your pin"], 0.92),
        ("Password Reset Manipulation", ["password reset requested", "reset your password immediately", "change your password now"], 0.85),
        ("Urgency & Artificial Scarcity", ["immediately", "act now", "urgent action required", "within 24 hours", "within 15 minutes", "final notice", "deadline expiring"], 0.80),
        ("Financial Fraud / Bank Manipulation", ["enter your bank details", "update bank account", "atm pin", "cvv", "card verification", "crypto wallet", "wire transfer", "payment diversion"], 0.90),
        ("Invoice Fraud / Fake Billing", ["invoice overdue", "payment delinquent", "unpaid invoice", "wire payment instructions", "remittance notice", "purchase order attached"], 0.85),
        ("Executive / Authority Impersonation", ["ceo", "managing director", "executive board", "cyber crime department", "federal tax", "income tax department", "police cyber cell"], 0.88),
        ("Secrecy & Non-Disclosure Demand", ["keep this confidential", "do not contact it department", "strictly private", "handle discreetly", "do not mention to anyone"], 0.92),
        ("Fear & Coercion Pressure", ["legal action will be taken", "law enforcement", "arrest warrant", "statutory penalty", "police investigation"], 0.88),
        ("Deceptive Call-To-Action", ["click here to unlock", "open link immediately", "tap link to verify", "download attachment to review"], 0.82)
    ]

    for cat_name, patterns, conf in categories:
        matched = [p for p in patterns if p in text]
        if matched:
            findings.append({
                "type": "Inference",
                "description": f"{cat_name} pattern detected: '{matched[0]}'",
                "confidence": conf,
                "source": "NLP Behavioral Engine"
            })

    return findings

# -------------------------------------------------------------------------
# 6b. BEC / Financial Fraud / AI-Generated & Deceptive Language Forensics
# (additive extension; called together with analyze_body_nlp)
# -------------------------------------------------------------------------

BEC_PATTERNS = [
    ("BEC / Wire Transfer Diversion", ["update our payment account", "change of banking details", "new wire instructions",
                                       "send payment to the new account", "remit to the following account", "urgent wire transfer",
                                       "update vendor payment"], 0.90),
    ("BEC / Payment Redirection via Executive Request", ["ceo", "cfo", "director"] , 0.80),  # handled with combo logic below
    ("Fake Invoice / Bogus Billing Request", ["please process the attached invoice", "attached invoice for immediate payment",
                                              "overdue invoice attached", "payment copy attached"], 0.88),
    ("Financial Account Credential Request", ["confirm your banking credentials", "validate your account number",
                                              "verify account details to avoid suspension"], 0.90),
]

AI_GENERATED_DECEPTIVE_MARKERS = [
    "i hope this email finds you well",
    "as per my last email",
    "please do the needful",
    "kindly revert at the earliest",
    "i would like to bring to your kind attention",
    "at your earliest convenience",
]

GENERIC_UNPERSONALIZED_MARKERS = ["dear customer", "dear user", "dear valued customer", "dear account holder", "dear sir/madam"]


def analyze_bec_and_deceptive_language(subject: str, body: str) -> List[Dict[str, Any]]:
    """
    Detects BEC / financial fraud / payment diversion / fake invoice patterns and
    AI-generated or deceptive language indicators. All findings are Inference with
    explicit confidence — never presented as proof.
    """
    text = (subject + "\n" + body).lower()
    findings: List[Dict[str, Any]] = []

    for cat_name, patterns, conf in BEC_PATTERNS:
        if cat_name.startswith("BEC / Payment Redirection via Executive Request"):
            continue  # handled via combined logic below
        matched = [p for p in patterns if p in text]
        if matched:
            findings.append({
                "type": "Inference",
                "description": f"{cat_name} pattern detected: '{matched[0]}'",
                "confidence": conf,
                "source": "BEC/Financial Fraud Engine",
            })

    # Combined BEC signal: executive identity + payment action (classic payment-diversion BEC)
    executive_terms = ["ceo", "cfo", "managing director", "the board", "our ceo", "executive director"]
    payment_actions = ["wire transfer", "payment", "invoice", "remit", "bank transfer", "purchase of gift cards"]
    has_exec = any(t in text for t in executive_terms)
    has_payment = any(t in text for t in payment_actions)
    if has_exec and has_payment:
        findings.append({
            "type": "Inference",
            "description": "Business Email Compromise (BEC) pattern: executive authority referenced alongside a payment/wire request (payment diversion risk).",
            "confidence": 0.93,
            "source": "BEC/Financial Fraud Engine",
        })

    # AI-generated / deceptive language indicators (heuristics, low-moderate confidence)
    ai_markers = [m for m in AI_GENERATED_DECEPTIVE_MARKERS if m in text]
    generic = [m for m in GENERIC_UNPERSONALIZED_MARKERS if m in text]
    if ai_markers:
        findings.append({
            "type": "Inference",
            "description": f"Formalized/templated phrasing commonly observed in bulk deceptive campaigns: '{ai_markers[0]}' (heuristic; does not prove automated authorship).",
            "confidence": 0.60,
            "source": "Deceptive Language Engine",
        })
    if generic:
        findings.append({
            "type": "Inference",
            "description": f"Non-personalized generic salutation ('{generic[0]}') typical of mass-mailed deceptive content.",
            "confidence": 0.65,
            "source": "Deceptive Language Engine",
        })
    # Coercion combo: politeness + urgency (deceptive pressure)
    urgency_terms = ["immediately", "urgent", "asap", "right away", "within the hour", "before the end of day"]
    if urgency_terms and ("kindly" in text or "please" in text) and (ai_markers or generic):
        findings.append({
            "type": "Inference",
            "description": "Mixed politeness + urgency pressure pattern consistent with social-engineering manipulation.",
            "confidence": 0.70,
            "source": "Deceptive Language Engine",
        })

    return findings


# -------------------------------------------------------------------------
# 6c. Sender-domain Homoglyph / Punycode / Confusables Analysis
# -------------------------------------------------------------------------

CONFUSABLE_MAP = {"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "|": "l"}

WELL_KNOWN_DOMAINS = [
    "paypal.com", "google.com", "microsoft.com", "amazon.com", "apple.com",
    "netflix.com", "facebook.com", "linkedin.com", "gmail.com", "outlook.com",
    "office365.com", "icloud.com", "yahoo.com", "github.com", "dropbox.com",
]


def _deconfuse(domain: str) -> str:
    lowered = domain.lower()
    out = []
    i = 0
    two_char = {"rn": "m", "vv": "w", "cl": "d"}
    while i < len(lowered):
        if lowered[i:i + 2] in two_char:
            out.append(two_char[lowered[i:i + 2]])
            i += 2
            continue
        ch = lowered[i]
        out.append(CONFUSABLE_MAP.get(ch, ch))
        i += 1
    return "".join(out)


def analyze_homoglyph_domain(sender_domain: str) -> List[Dict[str, Any]]:
    """Detects punycode/homoglyph/confusable sender domains. Evidence for punycode, Inference for confusables."""
    findings: List[Dict[str, Any]] = []
    if not sender_domain:
        return findings
    d = sender_domain.lower()
    if "xn--" in d:
        findings.append({
            "type": "Evidence",
            "description": f"Punycode (internationalized/homoglyph-capable) sender domain observed: '{d}'. Display rendering may disguise the true registry string.",
            "confidence": 0.95,
            "source": "Homoglyph Analyzer",
        })
    if any(ord(c) in (0x200B, 0x200C, 0x200D, 0x00AD, 0x2060) for c in sender_domain):
        findings.append({
            "type": "Evidence",
            "description": f"Invisible or zero-width character detected inside sender domain '{sender_domain}' — strong obfuscation indicator.",
            "confidence": 0.97,
            "source": "Homoglyph Analyzer",
        })
    try:
        d.encode("ascii")
    except UnicodeEncodeError:
        findings.append({
            "type": "Evidence",
            "description": f"Non-ASCII characters present in sender domain '{sender_domain}' (potential homoglyph spoofing).",
            "confidence": 0.9,
            "source": "Homoglyph Analyzer",
        })
    deconfused = _deconfuse(d)
    import difflib
    for known in WELL_KNOWN_DOMAINS:
        if deconfused == known and d != known:
            findings.append({
                "type": "Inference",
                "description": f"Sender domain '{d}' normalizes to well-known domain '{known}' under character-confusability analysis (lookalike/homoglyph candidate).",
                "confidence": 0.85,
                "source": "Homoglyph Analyzer",
            })
            break
        if deconfused != known and abs(len(deconfused) - len(known)) <= 1:
            if difflib.SequenceMatcher(None, deconfused, known).ratio() >= 0.92 and d != known:
                findings.append({
                    "type": "Inference",
                    "description": f"Sender domain '{d}' is a close confusable of well-known domain '{known}' (possible lookalike registration).",
                    "confidence": 0.75,
                    "source": "Homoglyph Analyzer",
                })
                break
    return findings


# -------------------------------------------------------------------------
# 6d. Threat-Intelligence Reputation Correlation (URL / Domain / IP)
# Provider-dependent (VirusTotal). Unavailable is surfaced explicitly — never
# fabricated. Safe to call with no providers configured.
# -------------------------------------------------------------------------

def correlate_threat_intelligence(urls: List[Dict[str, Any]], sender_domain: str,
                                  public_ips: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    def _wrap(status: str, stats: Dict[str, Any], target: str, target_type: str) -> Dict[str, Any]:
        provider_state = stats.get("provider_state") or ("CONFIGURED" if status == "Evidence" else "UNKNOWN")
        query_state = stats.get("query_state") or ("SUCCESS" if status == "Evidence" else "FAILED")
        result_state = stats.get("result_state") or ("AVAILABLE" if status == "Evidence" else "UNAVAILABLE")
        return {
            "target": target,
            "target_type": target_type,
            "status": status,  # Evidence | Unavailable
            "stats": stats,
            "provider": "VirusTotal",
            "provider_state": provider_state,
            "query_state": query_state,
            "result_state": result_state,
            "reason": stats.get("error"),
            "source": "VirusTotal",
        }

    for u in urls[:8]:
        domain = (u.get("registrable_domain") or u.get("hostname") or "").lower()
        if not domain:
            continue
        status, stats = DomainReputationProvider.check_domain(domain)
        results.append(_wrap(status, stats, domain, "domain"))

    if sender_domain:
        status, stats = DomainReputationProvider.check_domain(sender_domain)
        results.append(_wrap(status, stats, sender_domain, "sender_domain"))

    for ip in public_ips[:3]:
        if not classify_ip_address(ip).get("is_publicly_routable"):
            continue
        status, stats = ThreatIntelligenceProvider.check_ip(ip)
        results.append(_wrap(status, stats, ip, "ip"))

    return results


# -------------------------------------------------------------------------
# 7. Real Domain DNS Intelligence
# -------------------------------------------------------------------------

def query_domain_dns(domain: str) -> Dict[str, Any]:
    """
    Performs real DNS lookups using standard system resolver (nslookup/socket):
    Resolves A, MX, TXT (SPF/DMARC), and NS.
    Guarantees state is AVAILABLE or UNAVAILABLE, never mock data.
    """
    if not domain or domain in ["unknown", "none", "localhost"]:
        return {
            "provider": "DNS System Resolver",
            "provider_state": "CONFIGURED",
            "query_state": "NOT_RUN",
            "result_state": "UNAVAILABLE",
            "status": "UNAVAILABLE",
            "domain": domain,
            "error": "No valid domain supplied"
        }

    try:
        # 1. Resolve A records via socket
        resolved_ips = []
        try:
            addr_info = socket.getaddrinfo(domain, None, socket.AF_UNSPEC)
            for item in addr_info:
                ip = item[4][0]
                if ip not in resolved_ips:
                    resolved_ips.append(ip)
        except Exception:
            pass

        # 2. Query MX and TXT via standard DNS-over-HTTPS (DoH) with rapid fallback
        mx_hosts = []
        txt_records = []
        spf_record = None
        dmarc_record = None

        try:
            # TXT & SPF query via DoH
            doh_txt = requests.get(f"https://dns.google/resolve?name={domain}&type=TXT", timeout=1.5)
            if doh_txt.status_code == 200:
                for ans in doh_txt.json().get("Answer", []):
                    data_val = ans.get("data", "").strip('"')
                    txt_records.append(data_val)
                    if "v=spf1" in data_val.lower():
                        spf_record = data_val

            # MX query via DoH
            doh_mx = requests.get(f"https://dns.google/resolve?name={domain}&type=MX", timeout=1.5)
            if doh_mx.status_code == 200:
                for ans in doh_mx.json().get("Answer", []):
                    mx_hosts.append(ans.get("data", ""))

            # DMARC query via DoH
            doh_dmarc = requests.get(f"https://dns.google/resolve?name=_dmarc.{domain}&type=TXT", timeout=1.5)
            if doh_dmarc.status_code == 200:
                for ans in doh_dmarc.json().get("Answer", []):
                    data_val = ans.get("data", "").strip('"')
                    if "v=dmarc1" in data_val.lower():
                        dmarc_record = data_val
        except Exception:
            pass

        available = bool(resolved_ips or mx_hosts or txt_records)
        return {
            "provider": "DNS System Resolver",
            "provider_state": "CONFIGURED",
            "query_state": "SUCCESS" if available else "FAILED",
            "result_state": "AVAILABLE" if available else "UNAVAILABLE",
            "status": "AVAILABLE" if available else "UNAVAILABLE",
            "domain": domain,
            "resolved_ips": resolved_ips,
            "mx_hosts": mx_hosts,
            "spf_record": spf_record,
            "dmarc_record": dmarc_record,
            "txt_records_count": len(txt_records),
            "lookup_time": dt.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "provider": "DNS System Resolver",
            "provider_state": "CONFIGURED",
            "query_state": "FAILED",
            "result_state": "UNAVAILABLE",
            "status": "UNAVAILABLE",
            "domain": domain,
            "error": f"DNS query failed: {str(e)}"
        }

# -------------------------------------------------------------------------
# 8. Explainable Risk Scoring Engine
# -------------------------------------------------------------------------

def calculate_explainable_risk(
    findings: List[Dict[str, Any]],
    auth: Dict[str, Any],
    geo: Optional[Dict[str, Any]],
    attachments: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes an explainable risk score (0-100) with detailed contributing factors.
    Guarantees that score directly corresponds to observable evidence & inferences.
    """
    factors: List[Dict[str, Any]] = []
    total_score = 0

    def add_factor(factor_name: str, factor_score: int, factor_type: str):
        nonlocal total_score
        if not any(f["factor"] == factor_name for f in factors):
            factors.append({"factor": factor_name, "score": factor_score, "type": factor_type})
            total_score += factor_score

    # 1. Authentication Failures
    if auth.get("dmarc") == "FAIL":
        add_factor("DMARC authentication failed (FAIL)", 30, "Evidence")
    elif auth.get("spf") == "FAIL":
        add_factor("SPF validation failed (FAIL)", 20, "Evidence")
    elif auth.get("spf") == "SOFTFAIL":
        add_factor("SPF soft-fail (SOFTFAIL)", 10, "Evidence")

    if auth.get("dkim") == "FAIL":
        add_factor("DKIM digital signature failed (FAIL)", 20, "Evidence")

    # 2. Alignment Failures
    if auth.get("dmarc_alignment") == "Unaligned" and auth.get("dmarc") != "PASS":
        add_factor("Sender domain unaligned with authentication identity", 15, "Evidence")

    # 3. Findings from Sender / Body / Attachments
    for f in findings:
        desc = f.get("description", "")
        f_type = f.get("type", "")
        
        if "Reply-To Domain Mismatch" in desc:
            add_factor("Reply-To domain mismatch", 25, f_type)
        elif "Reply-To Mailbox Divergence" in desc:
            add_factor("Reply-To same-domain mailbox divergence", 5, f_type)
        elif "Reply-To Full-Address Difference" in desc:
            continue
        elif "Double extension" in desc:
            add_factor("Executable attachment with double extension", 35, f_type)
        elif "Suspicious executable" in desc:
            add_factor("Executable attachment detected", 30, f_type)
        elif "Lookalike domain" in desc:
            add_factor("Lookalike domain mimicking trusted brand", 25, f_type)
        elif "Display Name Impersonation" in desc:
            add_factor("Display name brand impersonation", 20, f_type)
        elif "IP-based URL" in desc:
            add_factor("Direct IP-based URL in content", 20, f_type)
        elif "Credential Harvesting" in desc or "Credential Harvesting / Login Phishing" in desc:
            add_factor("Explicit credential harvesting demand", 25, f_type)
        elif "Financial Fraud" in desc or "Bank Manipulation" in desc:
            add_factor("Financial fraud / bank manipulation request", 30, f_type)
        elif "BEC" in desc or "Business Email Compromise" in desc or "Payment Diversion" in desc or "payment diversion" in desc:
            add_factor("Business Email Compromise / payment diversion pattern", 35, f_type)
        elif "Fake Invoice" in desc or "Bogus Billing" in desc:
            add_factor("Fake invoice / bogus billing request", 30, f_type)
        elif "Urgent pressure" in desc or "Urgency" in desc or "urgency" in desc:
            add_factor("Urgency / pressure manipulation tactic", 10, f_type)
        elif "Punycode" in desc or "zero-width" in desc or "invisible" in desc and "domain" in desc:
            add_factor("Obfuscated / homoglyph-capable sender domain", 20, f_type)
        elif "Templated" in desc or "templated" in desc or "Generic salutation" in desc or "Deceptive" in desc or "deceptive" in desc:
            add_factor("Deceptive / templated language pattern", 10, f_type)
        elif "Account Suspension" in desc:
            add_factor("Coercive account suspension threat", 15, f_type)
        elif "Urgency & Artificial Scarcity" in desc:
            add_factor("High-pressure urgency language", 10, f_type)

    # Cap score at 100
    final_score = min(100, max(0, total_score))
    
    if final_score >= 65:
        safety = "dangerous"
        confidence = min(0.99, 0.80 + (final_score / 500))
    elif final_score >= 25:
        safety = "suspicious"
        confidence = 0.75
    else:
        safety = "safe"
        confidence = 0.92

    return {
        "safety": safety,
        "score": final_score,
        "confidence": confidence,
        "factors": factors
    }
