import email
from email import policy
import re
from typing import List, Dict, Any

def parse_headers(raw_email: str) -> Dict[str, Any]:
    """Parses raw email text and extracts important headers and Received chain."""
    try:
        msg = email.message_from_string(raw_email, policy=policy.default)
    except Exception as e:
        return {"error": str(e), "headers": {}, "received_chain": []}

    headers_extracted = {
        "From": msg.get("From", ""),
        "To": msg.get("To", ""),
        "Cc": msg.get("Cc", ""),
        "Reply-To": msg.get("Reply-To", ""),
        "Return-Path": msg.get("Return-Path", ""),
        "Subject": msg.get("Subject", ""),
        "Date": msg.get("Date", ""),
        "Message-ID": msg.get("Message-ID", ""),
        "Authentication-Results": msg.get("Authentication-Results", ""),
        "DKIM-Signature": msg.get("DKIM-Signature", ""),
        "X-Originating-IP": msg.get("X-Originating-IP", ""),
        "X-Mailer": msg.get("X-Mailer", ""),
        "User-Agent": msg.get("User-Agent", "")
    }

    # Extract all Received headers in order (bottom-up is chronological, but they are stored top-down)
    received_headers = msg.get_all("Received") or []
    
    # Parse received headers for basic IPs and hostnames
    received_chain = []
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    for header in received_headers:
        # Extract IPs (naive extraction, trace_engine will refine)
        ips = re.findall(ip_pattern, header)
        received_chain.append({
            "raw": header,
            "extracted_ips": ips
        })
        
    # Extract body for IOCs and further analysis
    body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body += part.get_content()
            elif part.get_content_type() == "text/html":
                html_body += part.get_content()
    else:
        if msg.get_content_type() == "text/plain":
            body = msg.get_content()
        elif msg.get_content_type() == "text/html":
            html_body = msg.get_content()
            
    if not body and html_body:
        body = html_body # Fallback

    return {
        "headers": headers_extracted,
        "received_chain": received_chain,
        "body": body,
        "html_body": html_body,
        "is_multipart": msg.is_multipart(),
        "parsed_successfully": True
    }
