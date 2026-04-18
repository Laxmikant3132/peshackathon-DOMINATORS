import psutil
import asyncio
from datetime import datetime
from core.common.schema import create_ues_event

class SafeEndpointSensor:
    """
    Real-time Endpoint Telemetry Sensor.
    Ingests live process data from the local OS using process_iter().
    Provides the 'Endpoint Layer' for XDR correlation.
    """
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.running = False
        self.seen_pids = set()

    async def start(self):
        self.running = True
        print("[SENSOR] Safe Endpoint Monitoring Started (Process Tracking)")
        
        while self.running:
            try:
                # Capture all active processes
                for proc in psutil.process_iter(['pid', 'name', 'username', 'ppid']):
                    try:
                        pinfo = proc.info
                        pid = pinfo['pid']
                        
                        # Monitor new processes or state changes
                        if pid not in self.seen_pids:
                            self.seen_pids.add(pid)
                            
                            event = create_ues_event(
                                sensor="psutil_process",
                                event_type="process_spawn",
                                source=str(pid),
                                target=pinfo['name'],
                                priority="LOW",
                                username=pinfo['username'],
                                ppid=pinfo['ppid']
                            )
                            await self.queue.put(event)
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Dynamic cleanup to keep seen_pids manageable
                if len(self.seen_pids) > 1000:
                    self.seen_pids.clear()
                    
            except Exception as e:
                print(f"[ENDPOINT SENSOR ERROR] {e}")
            
            await asyncio.sleep(5) # Polling interval for process discovery

    def stop(self):
        self.running = False
