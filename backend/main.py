from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import asyncio
from threat_engine import threat_engine_instance, simulator_instance
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
from typing import List, Optional
import os
from urllib.parse import urlparse
import difflib
import subprocess
import json
import random
from datetime import datetime as dt

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

class EmailInput(BaseModel):
    emailBody: str
    sender: str
    subject: str


class URLInput(BaseModel):
    url: str

class UPIInput(BaseModel):
    upi: str

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


# ML model for email classification (trained on phishing_email.csv dataset)
import joblib as _jl
_email_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "email_classifier.joblib")
try:
    model = _jl.load(_email_model_path)
    print(f"[ML] Email classifier loaded from {_email_model_path}")
except Exception as _e:
    print(f"[ML WARNING] Could not load email model: {_e}")
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
    full_text = (body + " " + subject).lower()

    # High-Risk Keywords
    critical_keywords = [
        "share otp", "send otp", "enter password", "provide otp", "enter your upi pin",
        "confirm your upi pin", "share your pin", "verify your password", "enter your bank details",
        "share card number", "enter cvv", "atm pin required", "account will be blocked",
        "account suspended", "permanent block", "scam", "phishing", "fraudulent",
        "identity theft", "security breach", "unauthorized login", "unusual activity"
    ]

    # Medium-Risk Keywords
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
        "failure to verify will result in suspension", "malicious", "fake",
        "dangerous", "suspicious", "verify-account", "update-now", "login-security",
        "account-alert", "secure-payment", "bit.ly", "tinyurl.com", "cutt.ly", "t.co", "ow.ly", "is.gd"
    ]
    
    for kw in critical_keywords:
        if kw in full_text:
            indicators.append(f"Critical: {kw}")

    for kw in suspicious_keywords:
        if kw in full_text:
            indicators.append(f"Suspicious: {kw}")

    # Subject Line Specific Threats
    subject = subject.lower()
    subject_threats = ["urgent", "action required", "blocked", "suspended", "notice", "alert", "security"]
    if any(st in subject for st in subject_threats):
        indicators.append("Aggressive/Deceptive Subject Line")

    # Domain Spoofing Detection
    is_spoofed, brand_name = check_domain_mismatch(sender, body, subject)
    if is_spoofed:
        indicators.append(f"Domain Spoofing: {brand_name} impersonation") 

    # Detect Urgency + Action Required Combination
    urgency = ["urgent", "immediately", "act now", "minutes", "hours", "warning"]
    action = ["click", "verify", "login", "update", "link", "provide", "enter"]
    
    if any(u in full_text for u in urgency) and any(a in full_text for a in action):
        indicators.append("Urgent pressure tactic detected")

    return indicators

# =========================
# EMAIL CLASSIFIER
# =========================

@app.post("/api/classify-email", response_model=ClassificationResponse)
async def classify_email(email: EmailInput):
    body = email.emailBody
    sender = email.sender
    subject = email.subject
    
    indicators = analyze_phishing_indicators(body, subject, sender)
    is_legit = is_legitimate_notification(body)

    # ML model check removed per user request

    # Reduce indicators if it looks like a legitimate notification
    if is_legit and indicators:
        # If it's a known legit pattern, we can be more lenient
        pass # Or potentially remove an indicator if you want fine-grained control


    # Decision Logic based on indicator count
    indicator_count = len(set(indicators))

    # ML model classification (if available) — uses phishing_email.csv trained model
    ml_prediction = None
    ml_confidence = 0.0
    if model is not None:
        try:
            text = body + " " + subject
            ml_prediction = model.predict([text])[0]
            ml_proba = model.predict_proba([text])[0]
            ml_confidence = float(max(ml_proba))
        except Exception as ml_err:
            print(f"[ML CLASSIFY ERROR] {ml_err}")

    # Boost indicator count if ML model flags as dangerous with high confidence
    if ml_prediction == "dangerous" and ml_confidence > 0.75:
        indicator_count += 3
        indicators.append(f"ML Model: {ml_prediction} ({ml_confidence*100:.0f}%)")
    elif ml_prediction == "dangerous" and ml_confidence > 0.5:
        indicator_count += 1
        indicators.append(f"ML Model: {ml_prediction} ({ml_confidence*100:.0f}%)")

    if indicator_count > 3:
        prediction = "dangerous"
        confidence = min(0.99, 0.85 + (indicator_count * 0.02))
        reason = f"High-risk! {indicator_count} malicious indicators detected: {', '.join(set(indicators))[:200]}"
    elif 1 <= indicator_count <= 3:
        prediction = "suspicious"
        confidence = min(0.85, 0.6 + (indicator_count * 0.05))
        reason = f"Suspicious activity! {indicator_count} indicators found: {', '.join(set(indicators))[:150]}"
    else:
        prediction = "safe"
        confidence = 0.95
        reason = "The email appears to be legitimate based on current analysis filters."

    return {
        "safety": prediction,
        "confidence": confidence,
        "reason": reason,
        "indicators": list(set(indicators))
    }




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
    disk = ps.disk_usage("C:\\")
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

    # Dataset traffic loop — streams real malicious patterns from Dataset_resumido.csv
    async def dataset_traffic_loop():
        async for event, alert in simulator_instance.generate_dataset_traffic():
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
                disk = ps.disk_usage("C:\\")
                net = ps.net_io_counters()
                await manager.broadcast({
                    "type": "health",
                    "data": {
                        "cpu_percent": cpu,
                        "memory_percent": mem.percent,
                        "memory_used_gb": round(mem.used / (1024**3), 2),
                        "active_connections": len(ps.net_connections(kind='inet')),
                        "disk_percent": disk.percent,
                        "net_sent_mb": round(net.bytes_sent / (1024**2), 2),
                        "net_recv_mb": round(net.bytes_recv / (1024**2), 2),
                        "timestamp": dt.now().isoformat()
                    }
                })
            except Exception as e:
                print(f"[HEALTH BROADCAST ERROR] {e}")
            await asyncio.sleep(10)

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
        dataset_traffic_loop(),
        health_broadcast_loop(),
        process_inventory_loop()
    )


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)