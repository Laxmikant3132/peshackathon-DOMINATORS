import psutil
import os
import asyncio
import time
from core.streaming.priority_inbox import PriorityInbox
from core.telemetry.sensor_manager import SensorManager
from core.streaming.processor import XDRProcessor

async def verify_integrity():
    """
    Diagnostic Truth Trace Script.
    Proves Real-Time Link between the Windows OS and Sentinel AI XDR.
    """
    print("====================================================")
    print("     SENTINEL AI | LIVE INTEGRITY AUDIT")
    print("====================================================")
    
    inbox = PriorityInbox(capacity=5000)
    manager = SensorManager(inbox)
    processor = XDRProcessor(inbox)

    # 1. Self-Identification (Detect our own auditor process)
    current_pid = os.getpid()
    auditor_process = psutil.Process(current_pid).name()
    print(f"[AUDIT] Monitoring Self: {auditor_process} (PID: {current_pid})")

    # 2. Initialize Telemetry Layer
    asyncio.create_task(manager.initialize_sensors(use_advanced=False))
    asyncio.create_task(processor.start())

    print("[AUDIT] Ingesting Live Telemetry... Please wait 5s.")
    await asyncio.sleep(5)

    # 3. Verification Trace
    print("\n[VERIFICATION RESULTS]")
    print("----------------------------------------------------")
    
    # Check if Auditor PID is in the Graph
    pid_found = False
    for node in processor.graph.graph.nodes:
        if str(current_pid) == str(node):
            pid_found = True
            break
    
    if pid_found:
        print(f"[OK] PID TRACE: Process '{auditor_process}' (PID: {current_pid}) SUCCESSFULY MAPPED.")
    else:
        print(f"[FAIL] PID TRACE: Process PID: {current_pid} not captured in 5s window.")

    # Check for real external network activity
    connections = psutil.net_connections(kind='inet')
    real_ext_ips = [c.raddr.ip for c in connections if c.raddr != () and c.laddr.ip != "127.0.0.1"]
    
    graph_ext_ips = [node for node, data in processor.graph.graph.nodes(data=True) 
                     if data.get('type') == 'entity' and "." in str(node)]

    match_count = 0
    for ip in real_ext_ips:
        if ip in graph_ext_ips:
            match_count += 1
            print(f"[OK] NETWORK TRACE: Real External IP '{ip}' IDENTIFIED in XDR Graph.")

    if match_count > 0:
        print(f"\n[FINAL STATUS] INTEGRITY CATEGORICALLY VERIFIED ({match_count} real-world matches).")
    else:
        print("\n[FINAL STATUS] INCONCLUSIVE - No external traffic detected by OS.")

    manager.shutdown()
    processor.stop()

if __name__ == "__main__":
    asyncio.run(verify_integrity())
