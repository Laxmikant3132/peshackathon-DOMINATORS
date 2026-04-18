from core.detector_rules import (
    detect_brute_force, 
    detect_exfiltration, 
    detect_c2_beaconing, 
    detect_lateral_movement,
    detect_insider_threat
)

def run_detection(events):
    """
    Groups events by session_id and runs all detection rules with session isolation.
    """
    # Group by session
    grouped_events = {}
    for e in events:
        sid = e["session_id"]
        if sid not in grouped_events:
            grouped_events[sid] = []
        grouped_events[sid].append(e)
    
    all_alerts = []
    
    # Analyze each session in isolation
    for session_id, session_events in grouped_events.items():
        # Edge case: skip sessions with insufficient data
        if len(session_events) < 2:
            continue
            
        # Detection rules list
        rules = [
            detect_brute_force, 
            detect_exfiltration, 
            detect_c2_beaconing, 
            detect_lateral_movement,
            detect_insider_threat
        ]
        
        session_alerts = []
        for rule in rules:
            alert = rule(session_id, session_events)
            # Apply Confidence Floor (>= 0.80)
            if alert and alert.get("confidence", 0) >= 0.80:
                session_alerts.append(alert)
        
        # Deduplication: Rules are already designed to return at most one alert per type per session
        all_alerts.extend(session_alerts)

    # Final Sorting: Priority (High -> Low) then Timestamp (Asc)
    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_alerts.sort(key=lambda x: (priority_rank.get(x["priority"], 3), x["timestamp"]))
    
    return all_alerts

def get_executive_summary(alerts, total_sessions):
    """
    Generates a structured SOC summary.
    """
    summary = {
        "Total Sessions Analyzed": total_sessions,
        "Total Alerts Generated": len(alerts),
        "Alerts by Type": {},
        "Priority Breakdown": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
        "System Health": "THREATS DETECTED" if alerts else "SYSTEM HEALTHY"
    }
    
    for alert in alerts:
        a_type = alert["type"]
        summary["Alerts by Type"][a_type] = summary["Alerts by Type"].get(a_type, 0) + 1
        
        prio = alert["priority"]
        summary["Priority Breakdown"][prio] = summary["Priority Breakdown"].get(prio, 0) + 1
        
    return summary
