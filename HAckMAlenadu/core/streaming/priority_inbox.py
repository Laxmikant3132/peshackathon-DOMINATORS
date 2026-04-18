import asyncio
from core.common.schema import UnifiedEvent

class PriorityInbox:
    """
    Severity-Aware Ingestion Queue.
    Ensures that HIGH-priority attack signals are never lost during burst traffic,
    while LOW-priority logs are throttled or sampled under load.
    """
    def __init__(self, capacity=10000):
        # We use separate internal queues to enforce strict priority
        self.queues = {
            "HIGH": asyncio.Queue(),
            "MEDIUM": asyncio.Queue(),
            "LOW": asyncio.Queue()
        }
        self.capacity = capacity
        self.current_count = 0

    async def push(self, event: UnifiedEvent):
        prio = event.priority
        
        # Priority-Aware Drop Policy (v4.0 Logic)
        if self.current_count >= self.capacity:
            if prio == "LOW":
                # Throttling point: Drop low-priority noise
                return False
            elif prio == "MEDIUM":
                # Buffer full: delay processing but don't drop (backpressure)
                pass 
        
        await self.queues[prio].put(event)
        self.current_count += 1
        return True

    async def put(self, event: UnifiedEvent):
        """Standard queue alias for compatibility with sensor loops."""
        return await self.push(event)

    async def get_next(self) -> UnifiedEvent:
        """
        Always yields HIGH events first, then MEDIUM, then LOW.
        This ensures the Detection Engine sees critical threats first.
        """
        while True:
            for prio in ["HIGH", "MEDIUM", "LOW"]:
                if not self.queues[prio].empty():
                    self.current_count -= 1
                    return await self.queues[prio].get()
            
            await asyncio.sleep(0.1) # Yield to event loop if all queues empty
