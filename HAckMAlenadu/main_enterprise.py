import asyncio
import signal
import sys
from core.streaming.priority_inbox import PriorityInbox
from core.telemetry.sensor_manager import SensorManager
from core.streaming.processor import XDRProcessor

class SentinelXDRController:
    """
    Main entry point for Sentinel AI Enterprise XDR.
    Orchestrates sensors, streaming pipeline, and intelligence engines.
    """
    def __init__(self):
        self.inbox = PriorityInbox(capacity=5000)
        self.manager = SensorManager(self.inbox)
        self.processor = XDRProcessor(self.inbox)
        self.running = False

    async def start(self):
        self.running = True
        print("====================================================")
        print("         SENTINEL AI | ENTERPRISE XDR CORE          ")
        print("====================================================")
        
        # 1. Initialize Telemetry Sensors (with Fallback)
        await self.manager.initialize_sensors(use_advanced=False) # SafeMode default
        
        # 2. Start Processing Pipeline
        processor_task = asyncio.create_task(self.processor.start())
        heartbeat_task = asyncio.create_task(self.manager.monitor_health())

        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self):
        print("\n[SYSTEM] Initiating Graceful Shutdown...")
        self.running = False
        self.manager.shutdown()
        self.processor.stop()
        print("[SYSTEM] Sentinel AI Offline.")

if __name__ == "__main__":
    controller = SentinelXDRController()
    try:
        asyncio.run(controller.start())
    except KeyboardInterrupt:
        pass
