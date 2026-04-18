from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import List
from core.streaming.priority_inbox import PriorityInbox
from core.telemetry.sensor_manager import SensorManager
from core.streaming.processor import XDRProcessor
from core.common.schema import create_ues_event

app = FastAPI(title="Sentinel AI Enterprise XDR API")

# Enable CORS for React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- XDR CORE INITIALIZATION ---
inbox = PriorityInbox(capacity=5000)
manager = SensorManager(inbox)
processor = XDRProcessor(inbox)


class ConnectionManager:
    """Manages active WebSocket connections for real-time telemetry."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)


ws_manager = ConnectionManager()


async def event_broadcaster():
    """
    Drains the processor's outgoing event queue and pushes each event
    to all connected WebSocket dashboards as an EVENT message.
    """
    while True:
        event = await processor.get_next_broadcast_event()
        if event:
            payload = json.dumps({"type": "EVENT", "data": event})
            await ws_manager.broadcast(payload)
        else:
            await asyncio.sleep(0.05)


async def stats_broadcaster():
    """Broadcasts global metrics every 2 seconds."""
    while True:
        stats = {
            "processed_count": processor.processed_count,
            "incident_count": len(processor.incident_gen.active_incidents),
            "threat_level": (
                "CRITICAL"
                if any(
                    i.severity == "HIGH"
                    for i in processor.incident_gen.active_incidents.values()
                )
                else "STABLE"
            ),
        }
        await ws_manager.broadcast(json.dumps({"type": "STATS", "data": stats}))
        await asyncio.sleep(2)


@app.on_event("startup")
async def startup_event():
    """Starts the background XDR intelligence loop."""
    asyncio.create_task(manager.initialize_sensors(use_advanced=False))
    asyncio.create_task(processor.start())
    asyncio.create_task(stats_broadcaster())
    asyncio.create_task(event_broadcaster())


@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; receive commands from React UI if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/api/incidents")
async def get_incidents():
    return [i.to_dict() for i in processor.incident_gen.active_incidents.values()]


@app.post("/api/simulator/brute-force")
async def trigger_brute_force():
    for i in range(10):
        e = create_ues_event(
            "sim_engine", "login_attempt", "192.168.1.5", "admin-portal",
            priority="LOW", status="failed"
        )
        await inbox.push(e)
    return {"status": "triggered"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
