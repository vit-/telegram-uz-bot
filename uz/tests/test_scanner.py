import asyncio
import time
from datetime import datetime, timedelta

import pytest
from flaky import flaky

from uz import scanner, client


@flaky
class TestUZScannerLive(object):

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_scanner(self, source_station, destination_station):
        self._cb_id = None,
        self._session_id = None
        self._running = True

        cb_id = 'callback id'
        timeout = 20

        date = datetime.today() + timedelta(days=21)

        scan = scanner.UZScanner(self.success_cb)
        with client.UZClient() as uz:
            trains = await uz.list_trains(date, source_station, destination_station)
            train = trains[0]

            start_time = time.time()
            await scan.add_item(
                cb_id, 'firstname', 'lastname', date, source_station, destination_station,
                train.num)
            while self._running and (time.time() - start_time) < timeout:
                await asyncio.sleep(1)

            assert self._session_id
            assert self._cb_id == cb_id

    def success_cb(self, cb_id, session_id):
        self._cb_id = cb_id
        self._session_id = session_id
        self._running = False
