import asyncio
import time


async def reliable_async_sleep(delay):
    start = time.time()
    while time.time() - start < delay:
        await asyncio.sleep(5)
