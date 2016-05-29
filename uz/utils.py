import asyncio
import time


RESOLUTION = 5


async def reliable_async_sleep(delay):
    start = time.time()
    while time.time() - start < delay:
        await asyncio.sleep(RESOLUTION)
