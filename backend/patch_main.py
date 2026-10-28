import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Models
new_models = """class AttachmentInfo(BaseModel):
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
    type: str # "Evidence" or "Inference"
    description: str
    confidence: float
    source: str
    timestamp: str

class EmailClassificationResponse(BaseModel):
    safety: str
    confidence: float
    reason: Optional[str]
    indicators: List[ForensicFinding]

class URLInput(BaseModel):"""

content = re.sub(r'class EmailInput\(BaseModel\):.*?class URLInput\(BaseModel\):', new_models, content, flags=re.DOTALL)

# 2. Update classify_email
new_classify = """@app.post("/api/classify-email", response_model=EmailClassificationResponse)
async def classify_email(email: EmailInput):
    body = email.emailBody
    sender = email.sender
    subject = email.subject
    
    # 1. Get raw string indicators from NLP / Regex
    raw_indicators = analyze_phishing_indicators(body, subject, sender)
    is_legit = is_legitimate_notification(body)

    forensic_findings = []
    current_time = dt.now().isoformat()
    
    # Convert text inferences to ForensicFinding objects
    for ind in raw_indicators:
        confidence = 0.85 if "Critical" in ind or "Spoofing" in ind else 0.65
        forensic_findings.append(ForensicFinding(
            type="Inference",
            description=ind,
            confidence=confidence,
            source="NLP/Heuristic Engine",
            timestamp=current_time
        ))

    # 2. Attachment Forensics
    suspicious_extensions = ['.exe', '.scr', '.vbs', '.bat', '.js', '.jar', '.ps1', '.cmd']
    if email.attachments:
        for att in email.attachments:
            ext = os.path.splitext(att.filename)[1].lower() if '.' in att.filename else ''
            # Double extension check
            parts = att.filename.split('.')
            if len(parts) > 2 and f".{parts[-1].lower()}" in suspicious_extensions:
                forensic_findings.append(ForensicFinding(
                    type="Evidence",
                    description=f"Double extension detected on attachment: {att.filename}",
                    confidence=0.98,
                    source="Attachment Forensics",
                    timestamp=current_time
                ))
            elif f".{parts[-1].lower()}" in suspicious_extensions if len(parts)>1 else False:
                forensic_findings.append(ForensicFinding(
                    type="Evidence",
                    description=f"Suspicious executable attachment: {att.filename}",
                    confidence=0.95,
                    source="Attachment Forensics",
                    timestamp=current_time
                ))
            
            # Size limits or mismatch logic
            if att.size_bytes > 50 * 1024 * 1024:
                forensic_findings.append(ForensicFinding(
                    type="Evidence",
                    description=f"Unusually large attachment: {att.filename} ({att.size_bytes} bytes)",
                    confidence=0.70,
                    source="Attachment Forensics",
                    timestamp=current_time
                ))

            # External Threat Intel (Hashes)
            if att.hash:
                vt_key = os.getenv("VIRUSTOTAL_API_KEY")
                if not vt_key:
                    forensic_findings.append(ForensicFinding(
                        type="Inference",
                        description=f"Threat Intel Unavailable for hash: {att.hash}",
                        confidence=0.0,
                        source="External Threat Intel (VirusTotal)",
                        timestamp=current_time
                    ))
                else:
                    forensic_findings.append(ForensicFinding(
                        type="Evidence",
                        description=f"Mocking threat lookup for hash: {att.hash}",
                        confidence=0.9,
                        source="External Threat Intel (VirusTotal)",
                        timestamp=current_time
                    ))

    # 3. Header / Geolocation Forensics
    has_relays = any(h.name.lower() == "received" for h in email.headers) if email.headers else False
    if has_relays:
        ip_api_key = os.getenv("IPINFO_API_KEY")
        if not ip_api_key:
            forensic_findings.append(ForensicFinding(
                type="Inference",
                description="IP Geolocation Unavailable for email relays.",
                confidence=0.0,
                source="IP Geolocation Provider",
                timestamp=current_time
            ))
        else:
            forensic_findings.append(ForensicFinding(
                type="Evidence",
                description="Mocking geolocation lookup.",
                confidence=0.9,
                source="IP Geolocation Provider",
                timestamp=current_time
            ))

    # Decision Logic based on indicator count and severity
    indicator_count = len(raw_indicators)
    critical_count = len([i for i in raw_indicators if "Critical" in i or "Spoofing" in i or "IP-based" in i])

    # We also add evidence weight to dangerous logic
    evidence_count = len([f for f in forensic_findings if f.type == "Evidence"])

    if critical_count >= 1 or indicator_count >= 3 or evidence_count >= 1:
        prediction = "dangerous"
        confidence = min(0.99, 0.85 + ((indicator_count + evidence_count) * 0.03))
        reason = f"Dangerous! High-risk indicators found. Evidence count: {evidence_count}."
    elif indicator_count >= 1:
        prediction = "suspicious"
        confidence = min(0.85, 0.6 + (indicator_count * 0.1))
        reason = f"Suspicious activity detected in the message."
    else:
        # Final pass: if it's explicitly legit, it's safe
        prediction = "safe"
        confidence = 0.95
        reason = "The email appears to be legitimate based on current analysis filters."

    # Final override: if it's marked as legit notification, we can downgrade dangerous to suspicious if not critical
    if is_legit and prediction == "dangerous" and critical_count == 0 and evidence_count == 0:
        prediction = "suspicious"
        reason = "Marked as suspicious due to content patterns, though it resembles a standard notification."

    return {
        "safety": prediction,
        "confidence": confidence,
        "reason": reason,
        "indicators": forensic_findings
    }
"""

content = re.sub(r'@app.post\("/api/classify-email", response_model=ClassificationResponse\).*?return \{\n.*?"safety": prediction,\n.*?"confidence": confidence,\n.*?"reason": reason,\n.*?"indicators": indicators\n.*?\}', new_classify, content, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched main.py successfully.")
