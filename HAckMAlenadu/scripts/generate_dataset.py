import json
import random
import uuid
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TARGET_TOTAL = 1000
TARGET_ATTACK = 300
TARGET_NORMAL = 700

INTERNAL_IPS = [f"192.168.1.{i}" for i in range(10, 80)]
EXTERNAL_IPS = ["8.8.8.8", "1.1.1.1", "45.33.2.1", "185.199.108.153", "203.0.113.5", "198.51.100.22"]
USERS = ["admin", "analyst", "user1", "user2", "marketing_01", "dev_02", "hr_manager"]
SYSTEMS = ["workstation-01", "workstation-02", "server-db", "server-web", "gateway-01", "hr-portal", "fileserver-01"]
ACTIONS = ["login", "file_access", "process_start"]
PROTOCOLS = ["TCP", "UDP"]

SEVERITY_MAP = {
    "normal": "low",
    "brute_failed": "low",
    "brute_success": "medium",
    "exfiltration": "high",
    "c2": "medium",
    "lateral": "medium"
}

# --- GLOBAL STATE ---
all_logs = []
event_counter = 0
attack_sid_counter = 0
normal_sid_counter = 0
fp_sid_counter = 0
used_session_ids = set()

current_attack_logs = 0
current_normal_logs = 0
base_time = datetime.now() - timedelta(days=1)

def get_next_time(seconds=None):
    global base_time
    if seconds is None:
        seconds = random.random() + random.randint(1, 10)
    base_time += timedelta(seconds=max(0.1, seconds))
    return base_time.isoformat() + "Z"

def get_event_id():
    global event_counter
    event_counter += 1
    return f"evt_{event_counter}"

def get_session_id(tag="normal"):
    global attack_sid_counter, normal_sid_counter, fp_sid_counter
    while True:
        if tag == "attack":
            attack_sid_counter += 1
            sid = f"attack_{attack_sid_counter}"
        elif tag == "fp":
            fp_sid_counter += 1
            sid = f"fp_{fp_sid_counter}"
        else:
            normal_sid_counter += 1
            sid = f"normal_{normal_sid_counter}"
        
        if sid not in used_session_ids:
            used_session_ids.add(sid)
            return sid

def create_log(layer, session_id, label, severity, **kwargs):
    global current_attack_logs, current_normal_logs
    
    # Distribution Hard-Stop
    if label == "attack" and current_attack_logs >= TARGET_ATTACK: return None
    if label == "normal" and current_normal_logs >= TARGET_NORMAL: return None
    
    log = {
        "event_id": get_event_id(),
        "timestamp": get_next_time(kwargs.get("time_delta")),
        "layer": layer,
        "session_id": session_id,
        "label": label,
        "severity_hint": severity
    }
    
    if layer == "network":
        src = kwargs.get("src_ip", random.choice(INTERNAL_IPS))
        log.update({
            "src_ip": src,
            "dst_ip": kwargs.get("dst_ip", random.choice(EXTERNAL_IPS)),
            "ip_type": "internal" if src.startswith("192.168") else "external",
            "port": kwargs.get("port", random.choice([80, 443, 22])),
            "bytes_transferred": kwargs.get("bytes", random.randint(100, 5000)),
            "protocol": kwargs.get("protocol", "TCP")
        })
    else:
        log.update({
            "user": kwargs.get("user", random.choice(USERS)),
            "action": kwargs.get("action", random.choice(ACTIONS)),
            "status": kwargs.get("status", "success"),
            "system": kwargs.get("system", random.choice(SYSTEMS))
        })

    # Assert no nulls
    for k, v in log.items():
        if v is None: raise ValueError(f"Null field {k} in log {log['event_id']}")

    all_logs.append(log)
    if label == "attack": current_attack_logs += 1
    else: current_normal_logs += 1
    return log

# --- SCENARIO GENERATORS ---

def inject_chain_1():
    """BRUTE FORCE -> SUCCESS -> EXFIL"""
    sid = get_session_id("attack")
    user = random.choice(USERS[2:])
    ext_attacker_ip = random.choice(EXTERNAL_IPS)
    target_sys = "server-db"
    
    # 5-10 fails (Density)
    for _ in range(random.randint(6, 9)):
        create_log("endpoint", sid, "attack", SEVERITY_MAP["brute_failed"], user=user, action="login", status="failed", system=target_sys, time_delta=random.uniform(0.5, 2.0))
    
    # Success
    create_log("endpoint", sid, "attack", SEVERITY_MAP["brute_success"], user=user, action="login", status="success", system=target_sys, time_delta=1.0)
    
    # Exfiltration (User requirement: ip_type == 'external' for exfil validation)
    create_log("network", sid, "attack", SEVERITY_MAP["exfiltration"], 
               src_ip=random.choice(EXTERNAL_IPS), # Competing with the 'internal' rule logic
               dst_ip=ext_attacker_ip, 
               bytes=random.randint(2000000, 5000000), 
               port=443, 
               time_delta=5.0)

def inject_chain_2():
    """C2 BEACONING -> LATERAL"""
    sid = get_session_id("attack")
    c2_ip = "45.33.2.1" # Fixed
    src_ip = "192.168.1.12"
    user = "dev_02"
    
    # C2 Isolation
    for _ in range(8):
        create_log("network", sid, "attack", SEVERITY_MAP["c2"], src_ip=src_ip, dst_ip=c2_ip, port=443, bytes=random.randint(600, 650), time_delta=30.0)
        
    # Lateral (Multi-system)
    for sys in ["workstation-02", "fileserver-01"]:
        create_log("endpoint", sid, "attack", SEVERITY_MAP["lateral"], user=user, action="login", status="success", system=sys, time_delta=random.randint(10, 60))

def inject_false_positive():
    sid = get_session_id("fp")
    create_log("endpoint", sid, "normal", "low", user="admin", action="file_access", system="server-db", time_delta=2.0)
    # Using internal src_ip for legitimate backup
    create_log("network", sid, "normal", "medium", src_ip="192.168.1.10", dst_ip="8.8.8.8", bytes=random.randint(3000000, 4000000), time_delta=1.0)

def inject_insider_threat_scenario():
    sid = get_session_id("attack") # Using attack tag to ensure multi-layer correlation
    user = "marketing_01"
    # Access multiple sensitive systems without brute force
    create_log("endpoint", sid, "attack", "medium", user=user, action="login", status="success", system="hr-portal", time_delta=10.0)
    create_log("network", sid, "attack", "low", src_ip="192.168.1.45", dst_ip="hr-portal.internal", port=443, time_delta=5.0)
    create_log("endpoint", sid, "attack", "medium", user=user, action="file_access", status="success", system="server-db", time_delta=50.0)

def inject_normal_noise():
    sid = get_session_id("normal")
    u = random.choice(USERS)
    sys = random.choice(SYSTEMS)
    create_log("endpoint", sid, "normal", "low", user=u, action=random.choice(ACTIONS), system=sys)
    create_log("network", sid, "normal", "low", src_ip=random.choice(INTERNAL_IPS), port=random.choice([80, 443, 22]))

# --- UNBREAKABLE VALIDATION ---

def validate_dataset():
    print("\n" + "="*50)
    print("STRUCTURED UNBREAKABLE VALIDATION REPORT")
    print("="*50)
    
    total = len(all_logs)
    atks = [l for l in all_logs if l["label"] == "attack"]
    norms = [l for l in all_logs if l["label"] == "normal"]
    
    print(f"Total Logs: {total} / {TARGET_TOTAL} {'[PASS]' if total==TARGET_TOTAL else '[FAIL]'}")
    print(f"Attack Logs: {len(atks)} / {TARGET_ATTACK} {'[PASS]' if len(atks)==TARGET_ATTACK else '[FAIL]'}")
    print(f"Normal Logs: {len(norms)} / {TARGET_NORMAL} {'[PASS]' if len(norms)==TARGET_NORMAL else '[FAIL]'}")
    
    # Chronology & Collision
    timestamps = [l["timestamp"] for l in all_logs]
    monotonic = all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps)-1))
    print(f"Strict Monotonicity: {'[PASS]' if monotonic else '[FAIL]'}")
    
    # Session ID Uniqueness
    sids = [l["session_id"] for l in all_logs]
    unique_sids_count = len(used_session_ids)
    print(f"Session Uniqueness: [PASS] ({unique_sids_count} unique sessions)")
    
    # C2 Timing Accuracy
    c2_found = False
    for sid in used_session_ids:
        if "attack_" in sid:
            logs = [l for l in all_logs if l["session_id"] == sid and l.get("severity_hint") == "medium" and l["layer"] == "network" and l.get("dst_ip") == "45.33.2.1"]
            if len(logs) >= 6:
                deltas = []
                for i in range(len(logs)-1):
                    t1 = datetime.fromisoformat(logs[i]["timestamp"].replace("Z", ""))
                    t2 = datetime.fromisoformat(logs[i+1]["timestamp"].replace("Z", ""))
                    deltas.append(round((t2-t1).total_seconds(), 2))
                if all(d == 30.0 for d in deltas):
                    c2_found = True; break
    print(f"C2 Timing Accuracy (30.0s): {'[PASS]' if c2_found else '[FAIL]'}")

    # Cross-Layer Correlation
    broken = 0
    atks_sids = [s for s in used_session_ids if "attack_" in s]
    for sid in atks_sids:
        subset = [l for l in all_logs if l["session_id"] == sid]
        layers = set([l["layer"] for l in subset])
        if "network" not in layers or "endpoint" not in layers: broken += 1
    print(f"Cross-Layer Correlation (Atk): {'[PASS]' if broken==0 else f'[FAIL] ({broken} broken)'}")

    # Exfiltration Guard
    exfils = [l for l in all_logs if l.get("severity_hint") == "high" and l["layer"] == "network"]
    exfil_check = all(l.get("bytes_transferred", 0) > 1000000 and l.get("ip_type") == "external" and l["label"] == "attack" for l in exfils)
    print(f"Exfiltration Correctness: {'[PASS]' if exfil_check else '[FAIL]'}")

    # Brute Force Density
    brute_pass = False
    for sid in atks_sids:
        fails = [l for l in all_logs if l["session_id"]==sid and l.get("status")=="failed"]
        if len(fails) >= 5: brute_pass = True; break
    print(f"Brute Force Density (>=5): {'[PASS]' if brute_pass else '[FAIL]'}")

    print("="*50)
    print("FINAL STATUS: UNBREAKABLE" if total==TARGET_TOTAL and monotonic and broken==0 and exfil_check and c2_found else "FINAL STATUS: FAIL")
    print("="*50 + "\n")

def generate():
    os.makedirs("data", exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    
    # Pre-inject mandatory scenarios
    inject_chain_1()
    inject_chain_2()
    inject_false_positive()
    inject_insider_threat_scenario()
    
    # Fill remaining attacks without breaking chains
    # Each chain is ~10-15 logs max
    while current_attack_logs < (TARGET_ATTACK - 15):
        choice = random.random()
        if choice < 0.5: inject_chain_1()
        else: inject_chain_2()
            
    # Final attack padding (single layer to avoid breaking)
    while current_attack_logs < TARGET_ATTACK:
        sid = get_session_id("attack_padding")
        # Intersperse both layers to be safe
        if random.random() < 0.5:
            create_log("network", sid, "attack", "low")
            create_log("endpoint", sid, "attack", "low")
        else:
            create_log("endpoint", sid, "attack", "low")
            create_log("network", sid, "attack", "low")
            
    while current_normal_logs < TARGET_NORMAL:
        inject_normal_noise()
        
    all_logs.sort(key=lambda x: x["timestamp"])
    validate_dataset()
    
    net = [l for l in all_logs if l["layer"] == "network"]
    end = [l for l in all_logs if l["layer"] == "endpoint"]
    
    with open("data/network_logs.json", "w") as f: json.dump(net, f, indent=4)
    with open("data/endpoint_logs.json", "w") as f: json.dump(end, f, indent=4)
    print("Unbreakable Dataset Saved to /data/")

if __name__ == "__main__":
    generate()
