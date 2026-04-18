import uuid
from datetime import datetime
from typing import List, Dict, Any, Set

class IncidentObject:
    """
    The unified XDR Incident Object.
    Groups related graph-linked events into a single actionable story.
    """
    def __init__(self, entities: Set[str], events: List[Dict[str, Any]]):
        self.incident_id = f"INC-{str(uuid.uuid4())[:8].upper()}"
        self.created_at = datetime.utcnow()
        self.status = "OPEN"
        self.entities = list(entities)
        self.events = sorted(events, key=lambda x: x.get('timestamp'))
        
        # v4.0 Architect-Required Metadata
        self.root_cause = self.events[0].get('source_entity') if self.events else "Unknown"
        self.time_range = {
            "start": self.events[0].get('timestamp').isoformat() + "Z" if self.events else None,
            "end": self.events[-1].get('timestamp').isoformat() + "Z" if self.events else None
        }
        
        # Severity Seed for Detection Logic
        priorities = [e.get('priority', 'LOW') for e in events]
        if "HIGH" in priorities: self.severity = "HIGH"
        elif "MEDIUM" in priorities: self.severity = "MEDIUM"
        else: self.severity = "LOW"

    def to_dict(self):
        return {
            "incident_id": self.incident_id,
            "created_at": self.created_at.isoformat() + "Z",
            "status": self.status,
            "severity": self.severity,
            "root_cause": self.root_cause,
            "time_range": self.time_range,
            "entities": self.entities,
            "event_count": len(self.events),
            "summary": self._generate_summary()
        }

    def _generate_summary(self):
        types = set(e.get('type') for e in self.events)
        return f"Coordinated {', '.join(types)} activity involving {len(self.entities)} entities."

class IncidentGenerator:
    """
    Bridges the Graph Engine and the SOC Dashboard.
    Detects clusters of suspicious activity and promotes them to the Incident Layer.
    """
    def __init__(self):
        self.active_incidents = {} # incident_id -> IncidentObject

    def generate_from_cluster(self, cluster_entities: Set[str], graph_engine):
        """
        Extracts all events for a cluster and builds a unified Incident Object.
        """
        cluster_events = []
        for src in cluster_entities:
            # Extract edges from the graph for these entities
            if src in graph_engine.graph:
                for _, dst, data in graph_engine.graph.edges(src, data=True):
                    if dst in cluster_entities:
                        cluster_events.append(data)

        # Basic deduplication of incidents based on entity overlap
        for inc_id, inc_obj in self.active_incidents.items():
            if any(e in inc_obj.entities for e in cluster_entities):
                # Update existing incident
                inc_obj.entities = list(set(inc_obj.entities) | cluster_entities)
                # (Simple merge for prototype)
                return inc_obj

        # Create new incident if no overlap found
        new_inc = IncidentObject(cluster_entities, cluster_events)
        self.active_incidents[new_inc.incident_id] = new_inc
        return new_inc
