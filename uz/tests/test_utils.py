import time

import pytest

from uz import utils


@pytest.mark.asyncio
async def test_reliable_async_sleep(patch_sleep_resolution):
    delay = 2
    start = time.time()
    await utils.reliable_async_sleep(delay)
    assert time.time() - start > delay
