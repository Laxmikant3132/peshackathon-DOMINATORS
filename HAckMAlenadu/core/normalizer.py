from datetime import datetime

def normalize_log(log):
    """
    Normalizes both network and endpoint logs into a unified schema for detection.
    """
    normalized = {
        "event_id": log.get("event_id"),
        "timestamp": datetime.fromisoformat(log["timestamp"].replace("Z", "")),
        "layer": log.get("layer"),
        "session_id": log.get("session_id"),
        "label": log.get("label"),
        "severity_hint": log.get("severity_hint"),
        "event_type": log.get("layer")
    }
    
    if log.get("layer") == "network":
        normalized.update({
            "src_ip": log.get("src_ip"),
            "dst_ip": log.get("dst_ip"),
            "ip_type": log.get("ip_type"),
            "port": log.get("port"),
            "bytes": log.get("bytes_transferred", 0),
            "protocol": log.get("protocol"),
            # Ensure unified fields are null-safe
            "user": None,
            "action": None,
            "status": None,
            "system": None
        })
    else:
        normalized.update({
            "user": log.get("user"),
            "action": log.get("action"),
            "status": log.get("status"),
            "system": log.get("system"),
            # Ensure unified fields are null-safe
            "src_ip": None,
            "dst_ip": None,
            "ip_type": None,
            "port": None,
            "bytes": 0,
            "protocol": None
        })
        
    return normalized
