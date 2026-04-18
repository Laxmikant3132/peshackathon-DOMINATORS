import asyncio
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
import uuid
import psutil
import joblib
import os
import numpy as np
import socket

# --- MODELS & SCHEMAS ---

# --- MODELS & SCHEMAS ---

class ThreatCategory:
    BRUTE_FORCE = "Brute Force / Credential Stuffing"
    LATERAL_MOVEMENT = "Lateral Movement"
    DATA_EXFILTRATION = "Data Exfiltration"
    C2_BEACONING = "Command & Control (C2) Beaconing"
    SUSPICIOUS_RESOURCE = "Suspicious Resource Consumption"
    HIGH_RISK_TOOL = "Unauthorized Security Tool Detected"

class Severity:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

# Real-world indicators
HIGH_RISK_PROCESSES = {
    "nmap.exe": "Port Scanner toolkit",
    "wireshark.exe": "Packet Sniffer / Protocol Analyzer",
    "nc.exe": "Netcat (Reversed Shell potential)",
    "powershell.exe": "PowerShell (Analyzing for suspicious flags...)",
    "cmd.exe": "Command Prompt (Elevated access risk)",
    "mimikatz.exe": "Credential Dumping tool",
    "hydra.exe": "Password Cracking tool",
    "tightvnc.exe": "Remote Access Tool (Potential RAT)",
    "teamviewer.exe": "Remote Access Tool",
    "anydesk.exe": "Remote Access Tool"
}

SUSPICIOUS_PORTS = {21, 22, 23, 445, 3389, 4444, 8888, 9999}

import socket

def get_actual_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())

HOST_IP = get_actual_local_ip()
HOST_NAME = socket.gethostname()

# --- DETECTION ENGINE ---

class ThreatEngine:
    def __init__(self):
        self.active_suspicious_ips = {} # ip -> {first_seen, last_seen, activities, threats}
        self.all_events_buffer = [] # Sampled buffer for live view
        self.last_alert_cooldown = {} # (ip, category) -> timestamp
        self.lock = asyncio.Lock()
        self.ml_model_data = self._load_ml_model()

    def _load_ml_model(self):
        model_path = os.path.join(os.path.dirname(__file__), "models", "network_threat_model.joblib")
        if os.path.exists(model_path):
            try:
                return joblib.load(model_path)
            except Exception as e:
                print(f"[ML ERROR] Failed to load network model: {e}")
        return None

    def _eval_ml_threat(self, event: dict):
        """Uses the ML model trained on Dataset_resumido.csv to classify the event."""
        if not self.ml_model_data or event.get("layer") != "network":
            return None

        try:
            import pandas as pd
            model = self.ml_model_data['model']
            features = self.ml_model_data['features']
            le_proto = self.ml_model_data['le_proto']

            # Map event to model features
            proto_enc = le_proto.transform([event.get("protocol", "TCP")])[0]
            
            # Construct feature dict for DataFrame
            feature_dict = {}
            for f in features:
                if f == 'sport': feature_dict[f] = event.get("port", 0)
                elif f == 'dsport': feature_dict[f] = event.get("port", 0) # Approximation
                elif f == 'proto_enc': feature_dict[f] = proto_enc
                elif f == 'sbytes': feature_dict[f] = event.get("bytes", 0)
                elif f == 'dbytes': feature_dict[f] = 0
                elif f == 'dur': feature_dict[f] = event.get("duration", 1.0)
                else: feature_dict[f] = 0

            df_input = pd.DataFrame([feature_dict])
            
            prediction = model.predict(df_input)[0]
            probs = model.predict_proba(df_input)[0]
            confidence = probs.max()

            if prediction == 1 and confidence > 0.85:
                return {
                    "type": "ML-Detected Network Anomaly",
                    "severity": Severity.HIGH if confidence < 0.95 else Severity.CRITICAL,
                    "confidence": float(confidence),
                    "reason": f"Pattern matches known malicious traffic (ML Confidence: {confidence*100:.1f}%). Originating from {event.get('process', 'Unknown Process')}.",
                    "playbook": "Analyze packet payload, identify associated process, and rotate shared credentials if data exfiltration is suspected.",
                    "timestamp": datetime.now().isoformat() + "Z",
                    "indicators": ["Dataset Pattern Match", "Anomalous Port Flow"]
                }
        except Exception as e:
            # Silently fail ML eval if needed, but log if debugging
            # print(f"[ML EVAL ERROR] {e}")
            pass
        return None

    def normalize_event(self, raw_event: dict) -> dict:
        """Normalizes heterogeneous logs from Network, Endpoint, and App layers."""
        base = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat() + "Z",
            "layer": raw_event.get("layer"),
            "src_ip": raw_event.get("src_ip", "0.0.0.0"),
            "dst_ip": raw_event.get("dst_ip", "0.0.0.0"),
            "label": raw_event.get("label", "normal"),
            "action": raw_event.get("action", "FLOW_EVENT"),
            "detail": raw_event.get("detail", ""),
            "sensor": raw_event.get("sensor", "psutil_engine"),
            "status": raw_event.get("status", "success")
        }
        
        if base["layer"] == "network":
            base.update({
                "port": raw_event.get("port"),
                "protocol": raw_event.get("protocol", "TCP"),
                "bytes": raw_event.get("bytes", 0),
                "duration": raw_event.get("duration", 1.0),
                "flags": raw_event.get("flags", "S")
            })
        elif base["layer"] == "endpoint":
            base.update({
                "process": raw_event.get("process"),
                "ppid": raw_event.get("ppid"),
                "user": raw_event.get("user"),
                "file_access": raw_event.get("file_access"),
                "action": raw_event.get("action"),
                "cpu_usage": raw_event.get("cpu_usage", 0),
                "mem_usage": raw_event.get("mem_usage", 0)
            })
        elif base["layer"] == "application":
            base.update({
                "method": raw_event.get("method", "GET"),
                "endpoint": raw_event.get("endpoint"),
                "status_code": raw_event.get("status_code", 200),
                "user_agent": raw_event.get("user_agent"),
                "geolocation": raw_event.get("geolocation", "Unknown")
            })
            
        return base

    async def process_event(self, raw_event: dict) -> tuple[dict, Optional[dict]]:
        """Analyzes an event and returns (normalized_event, alert)."""
        event = self.normalize_event(raw_event)
        ip = event["src_ip"]
        
        async with self.lock:
            # Maintain suspicious state
            if ip not in self.active_suspicious_ips:
                self.active_suspicious_ips[ip] = {
                    "first_seen": event["timestamp"],
                    "events": [],
                    "threats": [],
                    "last_alert": None
                }
            
            ip_data = self.active_suspicious_ips[ip]
            ip_data["events"].append(event)
            # Keep only last 100 events per IP to prevent memory leak
            if len(ip_data["events"]) > 100:
                ip_data["events"].pop(0)

            # --- DETECTION RULES ---
            
            # 1. High Risk Tool Detection (REAL)
            alert = self._detect_high_risk_tool(event, ip_data)
            if not alert:
                # 2. Resource Anomaly (REAL)
                alert = self._detect_resource_anomaly(event, ip_data)
            if not alert:
                # 3. Brute Force Detection
                alert = self._detect_brute_force(ip_data)
            if not alert:
                # 4. Data Exfiltration
                alert = self._detect_exfiltration(ip_data)
            if not alert:
                # 5. C2 Beaconing
                alert = self._detect_beaconing(ip_data)
            if not alert:
                # 6. Lateral Movement
                alert = self._detect_lateral_movement(ip_data)
            
            # --- ML DATASET INTEGRATION ---
            if not alert and event.get("layer") == "network":
                alert = self._eval_ml_threat(event)

            # ANTI-SPAM COOLDOWN LOGIC
            if alert:
                category = alert["type"]
                cooldown_key = (ip, category)
                now = datetime.now()
                
                if cooldown_key in self.last_alert_cooldown:
                    last_fired = self.last_alert_cooldown[cooldown_key]
                    if (now - last_fired).total_seconds() < 60:
                        # Skip broadcasting the alert but keep the log
                        return event, None
                
                # First time or cooldown expired
                self.last_alert_cooldown[cooldown_key] = now
                alert["src_ip"] = ip
                ip_data["threats"].append(alert)
                ip_data["last_alert"] = alert
                return event, alert
            
            return event, None


    def _detect_high_risk_tool(self, event, ip_data):
        if event["layer"] == "endpoint" and event.get("process"):
            proc = event["process"].lower()
            if any(tool in proc for tool in HIGH_RISK_PROCESSES):
                return {
                    "type": ThreatCategory.HIGH_RISK_TOOL,
                    "severity": Severity.CRITICAL if "mimikatz" in proc or "hydra" in proc else Severity.HIGH,
                    "confidence": 0.99,
                    "reason": f"Active security or hacking tool detected on host: {event['process']} ({HIGH_RISK_PROCESSES.get(proc, 'Unauthorized binary')})",
                    "playbook": "Kill process immediately, isolate host, and audit user permissions.",
                    "timestamp": datetime.now().isoformat() + "Z",
                    "history": [e for e in ip_data["events"][-5:]]
                }
        return None

    def _detect_resource_anomaly(self, event, ip_data):
        if event["layer"] == "endpoint" and (event.get("cpu_usage", 0) > 90 or event.get("mem_usage", 0) > 80):
             return {
                "type": ThreatCategory.SUSPICIOUS_RESOURCE,
                "severity": Severity.MEDIUM,
                "confidence": 0.75,
                "reason": f"Process {event.get('process')} is consuming excessive resources (CPU: {event.get('cpu_usage')}%, RAM: {event.get('mem_usage')}%). Possible cryptominer or ransomware encryption routine.",
                "playbook": "Investigate process origin and command line arguments. Check for disk I/O spikes.",
                "timestamp": datetime.now().isoformat() + "Z",
                "history": [e for e in ip_data["events"][-5:]]
            }
        return None

    def _detect_brute_force(self, ip_data):
        events = [e for e in ip_data["events"] if e["layer"] == "endpoint" and e.get("action") == "login_failed"]
        if len(events) >= 10: 
            return {
                "type": ThreatCategory.BRUTE_FORCE,
                "severity": Severity.HIGH,
                "confidence": 0.90,
                "reason": f"Extremely high volume of failed login attempts ({len(events)}) detected from host. Indicates an active credential stuffing or brute force attack.",
                "playbook": "Lock the targeted user account and audit source IP via firewall logs.",
                "timestamp": datetime.now().isoformat() + "Z",
                "history": events[-5:]
            }
        return None

    def _detect_exfiltration(self, ip_data):
        total_bytes = sum([e.get("bytes", 0) for e in ip_data["events"] if e["layer"] == "network"])
        if total_bytes > 50 * 1024 * 1024: # 50MB
            return {
                "type": ThreatCategory.DATA_EXFILTRATION,
                "severity": Severity.CRITICAL,
                "confidence": 0.88,
                "reason": f"Host transferred {round(total_bytes/(1024*1024), 2)}MB in a short window. Potential data exfiltration detected.",
                "playbook": "Isolate host from network, shutdown high-traffic processes, and audit file access logs for sensitive data.",
                "timestamp": datetime.now().isoformat() + "Z",
                "history": [e for e in ip_data["events"][-5:]]
            }
        return None

    def _detect_beaconing(self, ip_data):
        net_events = [e for e in ip_data["events"] if e["layer"] == "network"]
        if len(net_events) < 5: return None
        
        intervals = []
        from datetime import datetime
        for i in range(len(net_events)-1):
            t1 = datetime.fromisoformat(net_events[i]["timestamp"].replace('Z', ''))
            t2 = datetime.fromisoformat(net_events[i+1]["timestamp"].replace('Z', ''))
            intervals.append(round((t2 - t1).total_seconds(), 1))
            
        if len(intervals) > 3 and all(abs(x - intervals[0]) < 0.5 for x in intervals):
            return {
                "type": ThreatCategory.C2_BEACONING,
                "severity": Severity.MEDIUM,
                "confidence": 0.85,
                "reason": f"IP is establishing periodic connections every {intervals[0]} seconds. Indicates a potential Command & Control beacon.",
                "playbook": "Inspect process associated with these connections. Blacklist destination IP.",
                "timestamp": datetime.now().isoformat() + "Z",
                "history": [e for e in ip_data["events"][-5:]]
            }
        return None

    def _detect_lateral_movement(self, ip_data):
        systems = set([e.get("dst_ip") for e in ip_data["events"] if e["layer"] == "network"])
        if len(systems) > 15: # Raised threshold to 15 to avoid loopback noise
            return {
                "type": ThreatCategory.LATERAL_MOVEMENT,
                "severity": Severity.HIGH,
                "confidence": 0.90,
                "reason": f"Activity detected across {len(systems)} unique systems in a short window. Indicates internal reconnaissance or propagation.",
                "playbook": "Scan source endpoint for unauthorized remote access tools (RATs) and disable user account.",
                "timestamp": datetime.now().isoformat() + "Z",
                "history": [e for e in ip_data["events"][-5:]]
            }
        return None

# --- SIMULATOR ---

class TrafficSimulator:
    def __init__(self, engine: ThreatEngine):
        self.engine = engine
        self.is_running = False
        self.ips = [f"192.168.1.{i}" for i in range(2, 50)]
        self.external_ips = [f"45.23.11.{i}" for i in range(1, 10)]

    def get_active_task_inventory(self):
        """Returns a snapshot of currently running tasks, sorted by recency."""
        tasks = []
        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cpu_percent', 'memory_percent', 'username']):
            try:
                pinfo = proc.info
                tasks.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'].upper(),
                    "create_time": pinfo['create_time'],
                    "cpu": round(pinfo['cpu_percent'] or 0, 1),
                    "memory": round(pinfo['memory_percent'] or 0, 1),
                    "user": pinfo['username'] or "system"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by creation time (newest at top)
        return sorted(tasks, key=lambda x: x['create_time'], reverse=True)[:50]

    async def generate_normal_traffic(self):
        # We will keep application level simulation here since it's hard to get random HTTP requests via psutil easily
        while self.is_running:
            raw = {
                "layer": "application",
                "src_ip": random.choice(self.ips),
                "dst_ip": random.choice(self.ips + self.external_ips),
                "label": "normal",
                "endpoint": random.choice(["/api/v1/profile", "/login", "/home", "/dashboard", "/api/data"]),
                "status_code": random.choice([200, 200, 200, 301, 404])
            }
            
            event, alert = await self.engine.process_event(raw)
            yield event, alert
            await asyncio.sleep(random.uniform(0.5, 2.0))

    async def generate_psutil_endpoint_traffic(self):
        seen_pids = set()
        while self.is_running:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'username', 'ppid']):
                    if not self.is_running: break
                    try:
                        pinfo = proc.info
                        pid = pinfo['pid']
                        
                        if pid not in seen_pids:
                            seen_pids.add(pid)
                            
                            # Get real process stats
                            try:
                                cpu_usage = proc.cpu_percent()
                                mem_usage = proc.memory_percent()
                            except:
                                cpu_usage = 0
                                mem_usage = 0

                            # Task-First Labeling: Use the executable name as the hero label
                            task_name = pinfo['name'].upper()
                            
                            raw = {
                                "layer": "endpoint",
                                "src_ip": HOST_IP,
                                "dst_ip": HOST_NAME,
                                "label": "normal",
                                "process": pinfo['name'],
                                "user": pinfo['username'] or "system",
                                "action": f"{task_name}", 
                                "ppid": pinfo['ppid'],
                                "sensor": "psutil_endpoint",
                                "status": "success",
                                "cpu_usage": round(cpu_usage, 1),
                                "mem_usage": round(mem_usage, 1)
                            }
                            
                            event, alert = await self.engine.process_event(raw)
                            yield event, alert
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if len(seen_pids) > 2000:
                    seen_pids.clear()
                    
            except Exception as e:
                print(f"[ENDPOINT SENSOR ERROR] {e}")
            
            await asyncio.sleep(1) # CRITICAL: 1-second precision for proper accuracy

    async def generate_psutil_network_traffic(self):
        last_reported = {} # conn_id -> timestamp
        while self.is_running:
            try:
                connections = psutil.net_connections(kind='inet')
                now = time.time()
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        # Create a unique ID for this connection
                        conn_id = f"{conn.laddr.ip}:{conn.laddr.port}->{conn.raddr.ip}:{conn.raddr.port}"
                        
                        # PULSE LOGIC: Report if new OR if 15 seconds have passed
                        if conn_id not in last_reported or (now - last_reported[conn_id]) > 15:
                            last_reported[conn_id] = now
                            
                            # DEEP FORENSICS: Resolve the PID to an actual Task Name
                            task_name = "NETWORK_TASK"
                            if conn.pid:
                                try:
                                    task_name = psutil.Process(conn.pid).name().upper()
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass

                            # Context-aware details
                            detail = "NETWORK_CONNECT"
                            if conn.raddr.port == 443: detail = "HTTPS_REQUEST"
                            elif conn.raddr.port == 80: detail = "HTTP_GET"
                            elif conn.raddr.port == 53: detail = "DNS_QUERY"
                            elif conn.raddr.port == 22: detail = "SSH_SESSION"

                            raw = {
                                "layer": "network",
                                "src_ip": conn.laddr.ip,
                                "dst_ip": conn.raddr.ip,
                                "label": "normal",
                                "port": conn.raddr.port,
                                "protocol": "TCP" if conn.type == 1 else "UDP",
                                "bytes": random.randint(100, 5000), 
                                "action": task_name,
                                "detail": detail,
                                "sensor": "psutil_network",
                                "status": "success",
                                "timestamp": datetime.now().isoformat() + "Z"
                            }
                            event, alert = await self.engine.process_event(raw)
                            yield event, alert
                
                # Cleanup old connections from memory after an hour
                if len(last_reported) > 5000:
                    current_time = time.time()
                    last_reported = {k: v for k, v in last_reported.items() if (current_time - v) < 3600}
                    
            except Exception as e:
                print(f"[NETWORK SENSOR ERROR] {e}")
            
            await asyncio.sleep(1)

    async def generate_dataset_traffic(self):
        """Streams real, high-fidelity malicious traffic from the dataset to trigger ML indicators."""
        csv_path = os.path.join(os.path.dirname(__file__), "dataset", "Dataset_resumido.csv")
        try:
            import pandas as pd
            df = pd.read_csv(csv_path, low_memory=False)
            label_col = 'Label' if 'Label' in df.columns else ('label' if 'label' in df.columns else None)
            if not label_col:
                return
            
            malicious_df = df[df[label_col] == 1]
            if malicious_df.empty: return
            
            while self.is_running:
                row = malicious_df.sample(1).iloc[0]
                
                raw = {
                    "layer": "network",
                    "src_ip": random.choice(self.external_ips),
                    "dst_ip": HOST_IP,
                    "label": "malicious",
                    "port": int(pd.to_numeric(row.get('dsport', 0), errors='coerce') or 0),
                    "protocol": str(row.get('proto', 'TCP')).upper(),
                    "bytes": int(pd.to_numeric(row.get('sbytes', 1000), errors='coerce') or 1000),
                    "duration": float(pd.to_numeric(row.get('dur', 1.0), errors='coerce') or 1.0),
                    "action": "DATASET_ATTACK_SIMULATION",
                    "detail": "EXTERNAL_MALICIOUS_FLOW",
                    "sensor": "dataset_streamer",
                    "status": "success",
                    "timestamp": datetime.now().isoformat() + "Z"
                }
                
                event, alert = await self.engine.process_event(raw)
                yield event, alert
                
                # Stream dataset anomalous traffic periodically
                await asyncio.sleep(random.uniform(5, 12))
        except Exception as e:
            print(f"[DATASET STREAM ERROR] {e}")

    async def simulate_brute_force(self):
        target_ip = "185.23.1.55" # Malicious IP
        for _ in range(12):
            raw = {
                "layer": "endpoint",
                "src_ip": target_ip,
                "user": "admin",
                "action": "login_failed",
                "label": "malicious"
            }
            event, alert = await self.engine.process_event(raw)
            yield event, alert
            await asyncio.sleep(0.2)

    async def simulate_exfiltration(self):
        target_ip = "192.168.1.15"
        # First, sensitive file access
        raw_access = {
            "layer": "endpoint",
            "src_ip": target_ip,
            "file_access": "/data/db_backup.sql",
            "process": "python.exe",
            "label": "malicious"
        }
        await self.engine.process_event(raw_access)
        yield raw_access, None
        
        # Then, large data transfer
        raw_net = {
            "layer": "network",
            "src_ip": target_ip,
            "dst_ip": "45.1.1.1",
            "bytes": 60 * 1024 * 1024,
            "label": "malicious"
        }
        alert = await self.engine.process_event(raw_net)
        yield raw_net, alert

    async def run_burst(self, event_queue: asyncio.Queue):
        """Generates a burst of 500+ events/second."""
        while self.is_running:
            for _ in range(50): # 50 events per batch
                raw = {
                    "layer": "network",
                    "src_ip": f"10.0.0.{random.randint(1, 254)}",
                    "bytes": random.randint(10, 100),
                    "label": "normal"
                }
                await self.engine.process_event(raw)
                await event_queue.put((raw, None))
            await asyncio.sleep(0.1) # 10 batches per second = 500 events/sec

# Global Instance
threat_engine_instance = ThreatEngine()
simulator_instance = TrafficSimulator(threat_engine_instance)
