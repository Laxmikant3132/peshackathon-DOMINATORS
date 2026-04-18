from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Any

class ForensicSnapshotEngine:
    """
    Evidence Snapshot System.
    Captures and structures a 120-second time-series window around 
    a security incident to provide SOC analysts with raw forensic context.
    """
    def __init__(self, max_buffer_size=5000):
        # Circular buffer to hold raw telemetry for forensic lookup
        self.event_buffer = deque(maxlen=max_buffer_size)

    def record_event(self, event_dict: Dict[str, Any]):
        """Caches every event flowing through the normalizer for forensic lookback."""
        self.event_buffer.append(event_dict)

    def capture_snapshot(self, incident_time: datetime, window_seconds: int = 120) -> Dict[str, Any]:
        """
        Extracts a window of +/- window_seconds/2 around the incident timestamp.
        """
        half_window = timedelta(seconds=window_seconds // 2)
        start_time = incident_time - half_window
        end_time = incident_time + half_window

        evidence = [
            e for e in self.event_buffer 
            if start_time <= e.get('timestamp') <= end_time
        ]

        return {
            "window_size": f"{window_seconds}s",
            "event_count": len(evidence),
            "spike_detected": len(evidence) > 50, # Simple heuristic for volume spikes
            "time_series_raw": evidence[:100] # Cap for dashboard performance
        }
