import numpy as np
from datetime import datetime
from core.common.schema import UnifiedEvent
from core.intelligence.rolling_graph import RollingGraphEngine
from sklearn.ensemble import IsolationForest

class HybridAnalyzer:
    """
    Hybrid Intelligence Layer.
    Combines deterministic security rules with unsupervised anomaly detection
    to detect both known attacks and zero-day deviations.
    """
    def __init__(self, graph_engine: RollingGraphEngine):
        self.graph_engine = graph_engine
        self.anomaly_model = IsolationForest(contamination=0.01)
        self.feature_vectors = []
        self._is_trained = False

    def analyze(self, event: UnifiedEvent, related_entities: set):
        """
        Main analysis entry point. Returns a list of triggered signals.
        """
        signals = []
        
        # 1. Rule-Based Detection (Deterministic Track)
        rule_signals = self._check_rules(event, related_entities)
        signals.extend(rule_signals)
        
        # 2. Anomaly Detection (Statistical Track)
        anomaly_signals = self._check_anomalies(event)
        signals.extend(anomaly_signals)
        
        return signals

    def _check_rules(self, event: UnifiedEvent, related: set):
        signals = []
        
        # Rule: Data Exfiltration Pattern
        if event.event_type == "network_connect":
            bytes_out = event.metadata.get("bytes_out", 0)
            if bytes_out > 5000000: # 5MB threshold for demo
                signals.append({
                    "rule": "Exfiltration: High Volume Metadata",
                    "weight": 0.8,
                    "mitre": "T1048",
                    "feature": "bytes_out"
                })
        
        # Rule: Unusual Port Sequence (C2 / Lateral)
        low_rep_ports = [4444, 1337, 31337, 8080]
        if event.metadata.get("port") in low_rep_ports:
            signals.append({
                "rule": "Persistence: Low-Reputation Port Access",
                "weight": 0.6,
                "mitre": "T1071",
                "feature": "destination_port"
            })
            
        return signals

    def _check_anomalies(self, event: UnifiedEvent):
        """
        Uses Isolation Forest to detect statistical outliers in connection volume/timing.
        """
        # Placeholder for real-time feature vectoring
        # In a real system, we'd maintain a state per entity
        return []

    def train_baseline(self, baseline_events):
        """
        Trains the anomaly detector on 'Normal' log history.
        """
        print("[ANALYZER] Characterizing Network Baseline...")
        # (Mock training for demo architecture)
        self._is_trained = True
