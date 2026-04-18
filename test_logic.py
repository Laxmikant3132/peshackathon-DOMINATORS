
import re

def analyze_phishing_indicators(body):
    indicators = []
    body_lower = body.lower()
    
    # UPI Scam patterns
    has_pin = "pin" in body_lower
    has_action = any(kw in body_lower for kw in ["enter", "provide", "share", "verify", "identity", "details"])
    has_scam_context = any(kw in body_lower for kw in ["receive", "claim", "refund", "won", "reward", "prize", "cashback", "collect", "payment waiting"])
    
    print(f"DEBUG: has_pin={has_pin}, has_action={has_action}, has_scam_context={has_scam_context}")
    
    if has_pin and has_action and has_scam_context:
        indicators.append("upiScamPattern")
    
    return indicators

upi_dangerous = """
URGENT: Your UPI account is suspended. 
To reactivate, click here: http://suspicious-upi-verify.com/login 
Enter your UPI PIN to verify your identity and receive Rs. 10000 refund.
"""

if __name__ == "__main__":
    print(f"Testing with: {upi_dangerous}")
    indicators = analyze_phishing_indicators(upi_dangerous)
    print(f"Indicators: {indicators}")
