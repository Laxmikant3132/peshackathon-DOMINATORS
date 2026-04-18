from datetime import timedelta

# --- CONFIGURATION & PRIORITY ---
PRIORITY_MAP = {
    "Data Exfiltration": "HIGH",
    "C2 Beaconing": "MEDIUM",
    "Lateral Movement": "MEDIUM",
    "Brute Force": "LOW"
}

def detect_brute_force(session_id, events):
    """
    Condition: >=5 consecutive failed logins followed by 1 success for same user.
    Window: 180s
    """
    logins = [e for e in events if e["layer"] == "endpoint" and e["action"] == "login"]
    if len(logins) < 6: return None
    
    # Sort events within session (Safety)
    logins.sort(key=lambda x: x["timestamp"])
    
    consecutive_fails = []
    for i in range(len(logins)):
        event = logins[i]
        
        if event["status"] == "failed":
            consecutive_fails.append(event)
        elif event["status"] == "success":
            # Check if we have enough preceding fails
            if len(consecutive_fails) >= 5:
                first_fail_time = consecutive_fails[0]["timestamp"]
                success_time = event["timestamp"]
                
                # Window check (3 mins)
                if (success_time - first_fail_time).total_seconds() <= 180:
                    user = event["user"]
                    # Ensure all fails were from same user
                    if all(f["user"] == user for f in consecutive_fails):
                        confidence = 0.95 if len(consecutive_fails) >= 8 else 0.85
                        return {
                            "type": "Brute Force",
                            "session_id": session_id,
                            "severity": "medium",
                            "priority": PRIORITY_MAP["Brute Force"],
                            "confidence": confidence,
                            "timestamp": first_fail_time.isoformat() + "Z",
                            "user": user
                        }
            # Reset fails if we see a success without enough fails
            consecutive_fails = []
            
    return None

def detect_exfiltration(session_id, events):
    """
    Condition: bytes > 1MB, ip_type == "external", label != "normal".
    """
    # Check if there was any successful login in this session (optional but adds context)
    has_login = any(e.get("action") == "login" and e.get("status") == "success" for e in events)
    
    for event in events:
        if event["layer"] == "network":
            if (event["bytes"] > 1000000 and 
                event["ip_type"] == "external" and 
                event["label"] != "normal"):
                
                return {
                    "type": "Data Exfiltration",
                    "session_id": session_id,
                    "severity": "high",
                    "priority": PRIORITY_MAP["Data Exfiltration"],
                    "confidence": 0.95 if has_login else 0.80,
                    "timestamp": event["timestamp"].isoformat() + "Z",
                    "target_ip": event["dst_ip"]
                }
    return None

def detect_c2_beaconing(session_id, events):
    """
    Condition: Same dst_ip, >=6 events, exactly 30s intervals.
    """
    net_events = [e for e in events if e["layer"] == "network" and e["label"] == "attack"]
    if len(net_events) < 6: return None
    
    # Group by destination IP
    by_dst = {}
    for e in net_events:
        dst = e["dst_ip"]
        if dst not in by_dst: by_dst[dst] = []
        by_dst[dst].append(e)
        
    for dst, logs in by_dst.items():
        if len(logs) < 6: continue
        logs.sort(key=lambda x: x["timestamp"])
        
        # Check for continuous 30s window
        contiguous_count = 1
        start_time = None
        
        for i in range(len(logs) - 1):
            t1 = logs[i]["timestamp"]
            t2 = logs[i+1]["timestamp"]
            delta = (t2 - t1).total_seconds()
            
            if abs(delta - 30.0) < 0.001:
                if contiguous_count == 1: start_time = t1
                contiguous_count += 1
                if contiguous_count >= 6:
                    return {
                        "type": "C2 Beaconing",
                        "session_id": session_id,
                        "severity": "medium",
                        "priority": PRIORITY_MAP["C2 Beaconing"],
                        "confidence": 0.98,
                        "timestamp": start_time.isoformat() + "Z",
                        "target_ip": dst
                    }
            else:
                contiguous_count = 1
                
    return None

def detect_lateral_movement(session_id, events):
    """
    Condition: Same user, >=2 unique systems accessed within 5 min window.
    """
    logins = [e for e in events if e["layer"] == "endpoint" and e["action"] == "login" and e["status"] == "success"]
    if len(logins) < 2: return None
    
    logins.sort(key=lambda x: x["timestamp"])
    
    # Check sliding window
    for i in range(len(logins)):
        window_start = logins[i]["timestamp"]
        user = logins[i]["user"]
        systems_accessed = {logins[i]["system"]}
        
        for j in range(i + 1, len(logins)):
            if (logins[j]["timestamp"] - window_start).total_seconds() > 300:
                break
            
            if logins[j]["user"] == user:
                systems_accessed.add(logins[j]["system"])
                
                if len(systems_accessed) >= 2:
                    return {
                        "type": "Lateral Movement",
                        "session_id": session_id,
                        "severity": "medium",
                        "priority": PRIORITY_MAP["Lateral Movement"],
                        "confidence": 0.90,
                        "timestamp": window_start.isoformat() + "Z",
                        "user": user
                    }
    return None

def detect_insider_threat(session_id, events):
    """
    Condition: Access to sensitive systems (hr-portal AND server-db) by non-admin user.
    """
    sensitive_access = [e for e in events if e.get("layer") == "endpoint" and e.get("system") in ["hr-portal", "server-db"]]
    if not sensitive_access: return None
    
    systems = set([e["system"] for e in sensitive_access])
    user = sensitive_access[0]["user"]
    
    # If a non-admin user hits both sensitive systems in one session
    if len(systems) >= 2 and user != "admin":
        return {
            "type": "Insider Threat",
            "session_id": session_id,
            "severity": "medium",
            "priority": "MEDIUM",
            "confidence": 0.82,
            "timestamp": sensitive_access[0]["timestamp"].isoformat() + "Z",
            "user": user
        }
    return None
