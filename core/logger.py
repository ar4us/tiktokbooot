import logging
import asyncio
import sys
import queue

_queue: queue.Queue | None = None
_loop: asyncio.AbstractEventLoop | None = None

async def _drain():
    global _queue
    if _queue is None:
        _queue = queue.Queue()
    
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    while True:
        try:
            # Use run_in_executor to not block the loop while waiting for the queue
            record = await asyncio.get_event_loop().run_in_executor(None, _queue.get)
            console_handler.emit(record)
        except Exception:
            pass

class AsyncHandler(logging.Handler):
    def emit(self, record):
        global _queue
        if _queue is None:
            print(f"[PRE-INIT] {record.levelname} - {record.getMessage()}", file=sys.stderr)
            return
        try:
            _queue.put(record)
        except Exception:
            pass

def setup(level: str = "INFO"):
    global _queue, _loop
    
    _queue = queue.Queue()
    _loop = asyncio.get_event_loop()

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = []
    root.addHandler(AsyncHandler())
    
    return _drain()


