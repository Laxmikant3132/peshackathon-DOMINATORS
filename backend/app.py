from fastapi import FastAPI
from pydantic import BaseModel
import re
from typing import List
from urllib.parse import urlparse

app = FastAPI()

class EmailInput(BaseModel):
    emailBody: str

class ClassificationResponse(BaseModel):
    safety: str
    confidence: float
    reason: str

# 1. Expanded Phishing Keyword Dataset
PHISHING_KEYWORDS = [
    # Account Verification
    "verify your account", "confirm your account", "account verification required",
    "verify activity", "confirm identity", "security verification", "validate account",
    "confirm your login", "verify session", "re-activate account", "action required: verify",
    "verify your identity", "account validation", "account confirmation",
    
    # Security Alerts
    "suspicious activity", "unusual login attempt", "recent sign-in attempt",
    "unauthorized login", "security alert", "suspicious login detected",
    "protect your account", "security notice", "account flagged", "security warning",
    "detected unusual activity", "login from unknown device",
    
    # Urgency / Pressure
    "act immediately", "urgent action required", "within 24 hours", "within 48 hours",
    "limited time", "immediate verification required", "avoid account suspension",
    "account will be deleted", "suspended immediately", "final notice", "urgent reminder",
    
    # Financial / Payment
    "update billing", "payment failed", "billing problem", "invoice attached",
    "refund request", "payment confirmation required", "transaction declined",
    "update payment method", "overdue payment", "payment notification",
    
    # Document Lures
    "document awaiting review", "pending document", "review document",
    "secure document portal", "document confirmation required", "review attached file",
    "view document", "shared a file with you", "signed document",
    
    # Credential Phishing
    "re-enter password", "confirm password", "login to verify", "confirm login details",
    "verify credentials", "password expired", "update your password", "change password now"
]

# 2. Suspicious URL Patterns
SUSPICIOUS_DOMAIN_PATTERNS = [
    "secure-account-verification", "account-review", "document-center",
    "security-update", "login-confirm", "verify-session", "secure-login",
    "account-verification", "update-security", "client-document-center"
]

URGENCY_PHRASES = [
    "urgent", "immediately", "act now", "limited time", "as soon as possible",
    "within 24 hours", "within 48 hours", "deadline"
]

CREDENTIAL_REQUEST_PHRASES = [
    "login", "username", "password", "credentials", "access", "re-enter", "sign in"
]

DOCUMENT_LURE_PHRASES = [
    "document", "attached", "portal", "review", "pending"
]

def extract_urls(text: str) -> List[str]:
    # Extract URLs using regex: https?://\S+
    return re.findall(r'https?://\S+', text)

def analyze_email(body: str):
    score = 0
    detected_indicators = []
    body_lower = body.lower()
    
    # 1. Phishing keyword detection (+15 each)
    matched_keywords = []
    for kw in PHISHING_KEYWORDS:
        if kw in body_lower:
            score += 15
            matched_keywords.append(kw)
    
    if matched_keywords:
        detected_indicators.append("phishing keywords detected")

    # 2. Suspicious URL detection (+40)
    urls = extract_urls(body)
    suspicious_url_detected = False
    for url in urls:
        for pattern in SUSPICIOUS_DOMAIN_PATTERNS:
            if pattern in url.lower():
                suspicious_url_detected = True
                break
        if suspicious_url_detected:
            break
            
    if suspicious_url_detected:
        score += 40
        detected_indicators.append("suspicious domain detected")

    # 3. Urgency phrase detection (+20)
    if any(phrase in body_lower for phrase in URGENCY_PHRASES):
        score += 20
        detected_indicators.append("urgency detected")

    # 4. Unknown external domain (+20)
    if urls:
        score += 20
        detected_indicators.append("external links found")

    # 5. Credential request detection (+30)
    if any(phrase in body_lower for phrase in CREDENTIAL_REQUEST_PHRASES):
        score += 30
        detected_indicators.append("credential request detected")

    # 6. Document lure check (additional indicator for reason field)
    if any(phrase in body_lower for phrase in DOCUMENT_LURE_PHRASES):
        detected_indicators.append("document lure detected")

    # Final Classification
    # score < 30 → "safe", 30 ≤ score < 70 → "suspicious", score ≥ 70 → "dangerous"
    if score < 30:
        safety = "safe"
    elif 30 <= score < 70:
        safety = "suspicious"
    else:
        safety = "dangerous"

    # Confidence calculation: min(95, 20 + score)
    confidence = min(95, 20 + score) if score > 0 else 35.0
    if safety == "safe" and score == 0:
        confidence = 35.0

    return {
        "safety": safety,
        "confidence": float(confidence),
        "reason": ", ".join(list(dict.fromkeys(detected_indicators))) if detected_indicators else "No suspicious indicators found"
    }

@app.post("/api/classify-email", response_model=ClassificationResponse)
async def classify_email(email: EmailInput):
    result = analyze_email(email.emailBody)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
