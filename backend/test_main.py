from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def test_classify_email_safe():
    response = client.post("/api/classify-email", json={
        "emailBody": "Hi Team, we have a meeting tomorrow.",
        "sender": "boss@company.com",
        "subject": "Weekly Meeting"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["safety"] == "safe"

def test_classify_email_dangerous():
    response = client.post("/api/classify-email", json={
        "emailBody": "URGENT: Click here to enter your bank details and share OTP to verify your account or it will be suspended permanently.",
        "sender": "scam@fakebank.com",
        "subject": "Action Required: Account Blocked"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["safety"] == "dangerous"
    
    # Check that inferences are present
    has_inference = any(f["type"] == "Inference" for f in data["indicators"])
    assert has_inference

def test_classify_email_attachment_evidence():
    response = client.post("/api/classify-email", json={
        "emailBody": "See attached.",
        "sender": "scam@fakebank.com",
        "subject": "Invoice",
        "attachments": [
            {
                "filename": "invoice.pdf.exe",
                "size_bytes": 1024,
                "mime_type": "application/x-msdownload",
                "hash": "fakehash123"
            }
        ]
    })
    assert response.status_code == 200
    data = response.json()
    
    # Double extension is Evidence
    has_evidence = any(f["type"] == "Evidence" and "Double extension" in f["description"] for f in data["indicators"])
    assert has_evidence

def test_classify_email_unavailable_provider():
    # If we don't have the VT key, it should say Unavailable, NOT Inference.
    os.environ.pop("VIRUSTOTAL_API_KEY", None)
    response = client.post("/api/classify-email", json={
        "emailBody": "See attached.",
        "sender": "scam@fakebank.com",
        "subject": "Invoice",
        "attachments": [
            {
                "filename": "invoice.pdf",
                "size_bytes": 1024,
                "mime_type": "application/pdf",
                "hash": "fakehash123"
            }
        ]
    })
    assert response.status_code == 200
    data = response.json()
    
    has_unavailable = any(f["type"] == "Unavailable" for f in data["indicators"])
    assert has_unavailable

    # Verify no "Unavailable" was secretly classified as "Inference"
    has_inference_unavailable = any(f["type"] == "Inference" and ("Unavailable" in f["description"] or "configured" in f["description"]) for f in data["indicators"])
    assert not has_inference_unavailable

if __name__ == "__main__":
    test_classify_email_safe()
    test_classify_email_dangerous()
    test_classify_email_attachment_evidence()
    test_classify_email_unavailable_provider()
    print("All API tests passed.")
