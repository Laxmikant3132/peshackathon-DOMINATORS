import psutil
import time
import asyncio
from core.common.schema import create_ues_event

class SafeNetworkSensor:
    """
    Stabilized Network Sensor using OS-native psutil APIs.
    Zero-dependency, non-admin, and highly reliable for demo environments.
    """
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.running = False
        self.seen_connections = set()

    async def start(self):
        self.running = True
        print("[SENSOR] Safe Network Monitoring Started (psutil mode)")
        while self.running:
            try:
                # Capture current network connections
                connections = psutil.net_connections(kind='inet')
                for conn in connections:
                    # Ignore loopback for demo clarity unless needed
                    if conn.laddr.ip == "127.0.0.1" or conn.raddr == ():
                        continue
                    
                    conn_id = f"{conn.laddr.ip}:{conn.laddr.port}->{conn.raddr.ip}:{conn.raddr.port}"
                    if conn_id not in self.seen_connections:
                        self.seen_connections.add(conn_id)
                        
                        # Create UES Event
                        event = create_ues_event(
                            sensor="psutil_net",
                            event_type="network_connect",
                            source=conn.laddr.ip,
                            target=conn.raddr.ip,
                            priority="MEDIUM" if conn.raddr.port in [22, 3389, 4444] else "LOW",
                            port=conn.raddr.port,
                            protocol="TCP" if conn.type == 1 else "UDP",
                            pid=conn.pid
                        )
                        await self.queue.put(event)
                
                # Cleanup seen connections periodically (sliding window simulation)
                if len(self.seen_connections) > 1000:
                    self.seen_connections.clear()
                    
            except Exception as e:
                print(f"[SENSOR ERROR] {e}")
            
            await asyncio.sleep(2) # Polling interval for live metadata tracking

    def stop(self):
        self.running = False
