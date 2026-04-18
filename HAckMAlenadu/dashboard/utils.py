import json
import os
import pandas as pd
from datetime import datetime

def load_alerts():
    """Load alerts from data/alerts.json with basic parsing."""
    path = "data/alerts.json"
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []

def preprocess_alerts(alerts):
    """Convert to DataFrame and ensure proper typing."""
    if not alerts:
        return pd.DataFrame()
    df = pd.DataFrame(alerts)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Executive-friendly renaming
    df = df.rename(columns={
        'session_id': 'Attack Session',
        'type': 'Incident Type',
        'confidence': 'Detection Confidence'
    })
    return df

def calculate_threat_score(alerts):
    """Weighted sum of alerts: HIGH*3 + MEDIUM*2 + LOW*1."""
    score = 0
    for a in alerts:
        p = a.get("priority", "LOW")
        if p == "HIGH": score += 3
        elif p == "MEDIUM": score += 2
        else: score += 1
    return score

def generate_intelligent_story(session_alerts):
    """Translates a sequence of alerts into an executive narrative."""
    # Convert back to internal key names if they were renamed
    types = [a.get("type", a.get("Incident Type")) for a in session_alerts]
    
    if "Brute Force" in types and "Data Exfiltration" in types:
        return "🚩 **CRITICAL**: Credential compromise successfully escalated into a high-volume data breach. The attacker cracked an account and immediately began leaking sensitive assets."
    
    if "C2 Beaconing" in types and "Lateral Movement" in types:
        return "🕵️ **PERSISTENT**: Active persistence established via C2 beaconing. Attacker is currently moving across critical systems to identify high-value targets."
    
    if "Insider Threat" in types:
        return "⚠️ **INSIDER ANOMALY**: Legitimate user account accessing multiple high-value systems in a short window. This behavioral deviation indicates a potential insider threat or account misuse."

    if "Brute Force" in types:
        return "🔑 **ACCOUNT BREACH**: A successful login was achieved after multiple failed attempts. The account shold be considered compromised."
    
    if "Data Exfiltration" in types:
        return "💾 **DATA LEAK**: Unusually large volume of data recorded leaving the network to an external IP. Context suggests unauthorized exfiltration."

    if "C2 Beaconing" in types:
        return "📡 **MALICIOUS COMMS**: Command-and-control activity detected. System is communicating with a known malicious endpoint."
    
    return "📝 **SECURITY INCIDENT**: A sequence of high-confidence alerts has been correlated to this session, indicating an active threat."

def get_prevention_playbook(session_alerts):
    """Generates actionable next steps for the SOC analyst."""
    types = [a.get("type", a.get("Incident Type")) for a in session_alerts]
    steps = []
    
    if "Brute Force" in types:
        steps.append("🔐 **Identity**: Force password reset and enable MFA for the target user.")
    if "Data Exfiltration" in types:
        steps.append("🛑 **Network**: Terminate active connections and block the destination IP at the firewall.")
    if "C2 Beaconing" in types:
        steps.append("🖥️ **Endpoint**: Isolate the affected host from the network and begin forensic imaging.")
    if "Lateral Movement" in types:
        steps.append("🕵️ **Audit**: Expand log retention for all systems accessed in this session window.")
    if "Insider Threat" in types:
        steps.append("📂 **Access**: Temporarily suspend system permissions for the identified user until cleared.")
        
    if not steps:
        steps.append("🔍 **Investigation**: Monitor this session for further deviations from baseline behavior.")
        
    return steps

def get_session_badge(session_id):
    """Returns a visual marker icon for session types."""
    if not isinstance(session_id, str): return "⚪"
    if "attack" in session_id: return "🔴"
    if "fp" in session_id: return "🟡"
    return "🟢"
