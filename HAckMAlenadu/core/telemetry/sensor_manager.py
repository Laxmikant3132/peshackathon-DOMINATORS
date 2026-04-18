import asyncio
from core.telemetry.safe_network_sensor import SafeNetworkSensor
from core.telemetry.safe_endpoint_sensor import SafeEndpointSensor

class SensorManager:
    """
    Orchestrates telemetry collection and manages fail-safe fallback logic.
    Ensures that a crash in an 'advanced' sensor doesn't kill the entire SIEM.
    """
    def __init__(self, ingest_queue: asyncio.Queue):
        self.ingest_queue = ingest_queue
        self.active_sensors = []
        self.safe_mode = False

    async def initialize_sensors(self, use_advanced=False):
        """
        Attempts to start advanced sensors (scapy), but falls back to safe sensors (psutil)
        if any error occurs (e.g., missing Npcap, permission denied).
        """
        print("[MANAGER] Initializing Telemetry Layer...")
        
        # 1. Start Safe Network Sensor (psutil) -> Always ON as baseline
        safe_net = SafeNetworkSensor(self.ingest_queue)
        self.active_sensors.append(asyncio.create_task(safe_net.start()))

        # 2. Start Safe Endpoint Sensor (psutil) -> Provides process visibility
        safe_proc = SafeEndpointSensor(self.ingest_queue)
        self.active_sensors.append(asyncio.create_task(safe_proc.start()))
        
        # 2. Mock Advanced Sensor logic for architecture demonstration
        if use_advanced:
            try:
                # In a real impl, we'd import ScapySensor here
                print("[MANAGER] Attempting to mount Advanced Sensor (Scapy)...")
                # Simulate a failure to trigger the v4.0 Fail-Safe requirement
                raise PermissionError("Admin privileges required for Scapy Sniffing.")
            except Exception as e:
                print(f"[MANAGER FAIL-SAFE] Advanced Sensor failed ({e}). Falling back to SafeMode metadata.")
                self.safe_mode = True

        print(f"[MANAGER] Monitoring active. Mode: {'SAFE' if self.safe_mode else 'ENTERPRISE'}")

    async def monitor_health(self):
        """Monitors sensor heartbeats (Future implementation)."""
        while True:
            # Check if sensors are still pushing to queue
            await asyncio.sleep(10)

    def shutdown(self):
        print("[MANAGER] Shutting down sensors...")
        for sensor in self.active_sensors:
            sensor.cancel()
