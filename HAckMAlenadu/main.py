import json
import os
from core.normalizer import normalize_log
from core.detector_engine import run_detection, get_executive_summary

def load_json_logs(file_path):
    """Utility to load JSON logs safely."""
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found.")
        return []
    with open(file_path, "r") as f:
        return json.load(f)

def print_alerts(alerts):
    print("\n" + "="*60)
    print("                      DETECTED THREAT ALERTS")
    print("="*60)
    if not alerts:
        print("No threats detected.")
    for alert in alerts:
        print(f"[{alert['priority']}] {alert['type']} Detected")
        print(f"  Session ID: {alert['session_id']}")
        print(f"  Confidence: {alert['confidence']:.2f}")
        print(f"  Incident Time: {alert['timestamp']}")
        # Additional context
        if "user" in alert: print(f"  Target User: {alert['user']}")
        if "target_ip" in alert: print(f"  Target IP: {alert['target_ip']}")
        print("-" * 30)

def print_summary(summary):
    print("\n" + "="*60)
    print("                    SIEM EXECUTIVE SUMMARY")
    print("="*60)
    for key, value in summary.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_val in value.items():
                print(f"  - {sub_key}: {sub_val}")
        else:
            print(f"{key}: {value}")
    print("="*60 + "\n")

def main(save_json=True):
    print("Initializing SIEM Engine...")
    
    # 1. Data Ingestion
    network_raw = load_json_logs("data/network_logs.json")
    endpoint_raw = load_json_logs("data/endpoint_logs.json")
    
    # 2. Normalization & Global Sorting
    print(f"Normalizing {len(network_raw) + len(endpoint_raw)} logs...")
    all_normalized = [normalize_log(l) for l in network_raw + endpoint_raw]
    all_normalized.sort(key=lambda x: x["timestamp"])
    
    # 3. Detection & Correlation
    print("Running detection logic...")
    alerts = run_detection(all_normalized)
    
    # 4. Executive Reporting
    unique_sessions = len(set(l["session_id"] for l in all_normalized))
    summary = get_executive_summary(alerts, unique_sessions)
    
    # 5. Output Results
    print_alerts(alerts)
    print_summary(summary)

    # 6. Export for Dashboard
    if save_json:
        os.makedirs("data", exist_ok=True)
        with open("data/alerts.json", "w") as f:
            json.dump(alerts, f, indent=4)
        print(f"Alerts exported to data/alerts.json ({len(alerts)} items)")

if __name__ == "__main__":
    main()
