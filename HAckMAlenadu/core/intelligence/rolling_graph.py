import networkx as nx
from datetime import datetime, timedelta
from core.common.schema import UnifiedEvent
from collections import deque

class RollingGraphEngine:
    """
    Graph-Based Correlation Engine.
    Uses networkx to maintain a rolling-window state graph of entities (Nodes) 
    and security events (Edges).
    
    Optimized for real-time performance by bounding the graph to a 15-minute window.
    """
    def __init__(self, window_minutes=15):
        self.graph = nx.MultiDiGraph()
        self.window = timedelta(minutes=window_minutes)
        self.event_timestamps = deque() # Track (timestamp, node1, node2) for pruning

    def add_event(self, event: UnifiedEvent):
        """
        Processes a UES event into the graph. 
        Links entities (User -> Host, Host -> IP, etc.) to build the attack context.
        """
        src = event.source_entity
        dst = event.target_entity
        now = datetime.utcnow()

        # 1. Update Graph
        self.graph.add_node(src, type="entity", first_seen=event.timestamp)
        if dst:
            self.graph.add_node(dst, type="entity")
            self.graph.add_edge(src, dst, 
                               event_id=event.event_id,
                               type=event.event_type,
                               timestamp=event.timestamp,
                               priority=event.priority)
            
            # Record for rolling pruning
            self.event_timestamps.append((event.timestamp, src, dst))

        # 2. Pruning: Maintain 15-minute operational limit (v4.0 Requirement)
        self._prune_old_events(now)

    def _prune_old_events(self, current_time: datetime):
        """Removes nodes and edges that fall outside the rolling window."""
        while self.event_timestamps and (current_time - self.event_timestamps[0][0]) > self.window:
            ts, src, dst = self.event_timestamps.popleft()
            
            # 1. Remove the old edge
            if self.graph.has_edge(src, dst):
                # Using MultiDiGraph, we remove one edge instance with matching timestamp
                # For simplicity in prototype, we remove the first edge we find
                try:
                    self.graph.remove_edge(src, dst)
                except Exception:
                    pass

            # 2. Cleanup isolated nodes (Stale node removal)
            for node in [src, dst]:
                if node in self.graph and self.graph.degree(node) == 0:
                    self.graph.remove_node(node)

    def get_related_entities(self, entity_id: str) -> set:
        """Returns all entities connected to the given ID within the rolling window."""
        if entity_id not in self.graph:
            return set()
        return set(nx.descendants(self.graph, entity_id)) | set(nx.ancestors(self.graph, entity_id))

    def get_incident_cluster(self, start_node: str):
        """Identifies a high-correlation cluster (connected component) for incident building."""
        if start_node not in self.graph:
            return None
        # In an XDR context, the connected component represents the 'Impact Zone'
        undirected = self.graph.to_undirected()
        return nx.node_connected_component(undirected, start_node)
