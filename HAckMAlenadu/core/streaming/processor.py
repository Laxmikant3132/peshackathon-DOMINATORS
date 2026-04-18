import asyncio
from datetime import datetime
from core.streaming.priority_inbox import PriorityInbox
from core.intelligence.rolling_graph import RollingGraphEngine
from core.intelligence.hybrid_analyzer import HybridAnalyzer
from core.intelligence.incident_generator import IncidentGenerator
from core.response.contribution_engine import ContributionEngine
from core.response.forensic_snapshot import ForensicSnapshotEngine


class XDRProcessor:
    """
    The central intelligence bus for Sentinel AI Enterprise XDR.
    Orchestrates the flow from raw telemetry ingestion to incident building and forensic capture.
    """
    def __init__(self, inbox: PriorityInbox):
        self.inbox = inbox
        self.graph = RollingGraphEngine(window_minutes=15)
        self.analyzer = HybridAnalyzer(self.graph)
        self.incident_gen = IncidentGenerator()
        self.explainability = ContributionEngine()
        self.forensics = ForensicSnapshotEngine()

        self.running = False
        self.processed_count = 0
        self.alert_count = 0

        # Outbound broadcast queue: serializable event dicts for WebSocket clients
        self._broadcast_queue: asyncio.Queue = asyncio.Queue(maxsize=500)

    async def get_next_broadcast_event(self):
        """Non-blocking drain of the broadcast queue. Returns None if empty."""
        try:
            return self._broadcast_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def start(self):
        self.running = True
        print("[PROCESSOR] XDR Intelligence Pipeline Active. Monitoring stream...")

        while self.running:
            # 1. Consume from Severity-Aware Priority Inbox
            event = await self.inbox.get_next()
            if not event:
                await asyncio.sleep(0.1)
                continue

            self.processed_count += 1

            # 2. Feed Rolling Graph State (Entity Linking)
            self.graph.add_event(event)

            # 3. Push broadcast-ready dict to outbound queue (non-blocking)
            broadcast_data = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat() + "Z",
                "event_type": event.event_type,
                "source_entity": event.source_entity,
                "target_entity": event.target_entity,
                "priority": event.priority,
                "status": event.status,
                "sensor_type": event.sensor_type,
            }
            try:
                self._broadcast_queue.put_nowait(broadcast_data)
            except asyncio.QueueFull:
                # Drop oldest if queue is full to avoid backpressure
                try:
                    self._broadcast_queue.get_nowait()
                    self._broadcast_queue.put_nowait(broadcast_data)
                except Exception:
                    pass

            # 4. Analyze Patterns across Graph Window
            related_entities = self.graph.get_related_entities(event.source_entity)
            signals = self.analyzer.analyze(event, related_entities)

            # 5. Forensic Snapshot Capture (Windowed Evidence)
            self.forensics.record_event(event.dict())

            # 6. Incident Correlation & Explainability
            if signals:
                self.alert_count += 1
                cluster = self.graph.get_incident_cluster(event.source_entity)
                incident = self.incident_gen.generate_from_cluster(cluster, self.graph)
                breakdown = self.explainability.generate_breakdown(signals)
                confidence, reason = self.explainability.justify_confidence(len(signals), 0.8)
                snapshot = self.forensics.capture_snapshot(event.timestamp)
                print(f"[INCIDENT DETECTED] {incident.incident_id} | Type: {incident.summary}")
                print(f"  > Confidence: {confidence} | Reason: {reason}")
                print(f"  > Entities: {', '.join(incident.entities)}")

    def stop(self):
        self.running = False
        print("[PROCESSOR] Intelligence Pipeline Drained.")
