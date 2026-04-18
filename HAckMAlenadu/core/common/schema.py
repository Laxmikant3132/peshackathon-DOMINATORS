from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class UnifiedEvent(BaseModel):
    """
    Standardized schema for all Sentinel AI telemetry.
    Ensures that Network, Endpoint, and Application logs are correlated seamlessly.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Priority for the Streaming Queue: HIGH, MEDIUM, LOW
    priority: str = "LOW"
    
    # Entity Relationship Data (Source -> Target)
    source_entity: str  # e.g., "192.168.1.5", "admin_user", "workstation-01"
    target_entity: Optional[str] = None
    
    # Metadata for Graph Edge
    event_type: str  # e.g., "network_connect", "process_spawn", "identity_login"
    status: str = "success"
    
    # Enrichment Data
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sensor_type: str  # e.g., "psutil_net", "win_event_log", "scapy_deep"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

def create_ues_event(sensor: str, event_type: str, source: str, target: str = None, priority: str = "LOW", **kwargs):
    """Factory helper for creating UES events."""
    return UnifiedEvent(
        sensor_type=sensor,
        event_type=event_type,
        source_entity=source,
        target_entity=target,
        priority=priority,
        metadata=kwargs
    )
