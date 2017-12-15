import asyncio
import time
from datetime import datetime, timedelta

import mock
import pytest
from flaky import flaky

from uz.tests import AIOMock, Awaitable

from uz import scanner, client


# @flaky(max_runs=5)
class TestUZScannerLive(object):

    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_scanner(self, source_station, destination_station):
        self._cb_id = None,
        self._session_id = None
        self._running = True

        cb_id = 'callback id'
        timeout = 10

        date = datetime.today() + timedelta(days=20)

        scan = scanner.UZScanner(self.success_cb, delay=1)
        asyncio.ensure_future(scan.run())
        with client.UZClient() as uz:
            trains = await uz.list_trains(date, source_station, destination_station)
            train = trains[0]
            ct_letter = train.coach_types[-1].letter

            start_time = time.time()
            scan.add_item(
                cb_id, 'firstname', 'lastname', date, source_station, destination_station,
                train.num, ct_letter)
            while self._running and (time.time() - start_time) < timeout:
                await asyncio.sleep(1)

            assert self._cb_id == cb_id
            assert self._session_id

    def success_cb(self, cb_id, session_id):
        self._cb_id = cb_id
        self._session_id = session_id
        self._running = False


@pytest.mark.asyncio
async def test_run_stop(patch_sleep_resolution, source_station, destination_station):
    instance = scanner.UZScanner(mock.Mock(), 0)
    instance.scan = AIOMock()
    instance.session = mock.Mock()
    run_task = instance.run()
    asyncio.ensure_future(run_task)

    success_cb_id = 'id123'
    firstname = 'firstname'
    lastname = 'lastname'
    date = datetime(2016, 1, 1)
    train_num = '741K'
    ct_letter = 'C1'
    scan_id = instance.add_item(
        success_cb_id, firstname, lastname, date, source_station, destination_station,
        train_num, ct_letter)

    await asyncio.sleep(0)
    instance.scan.assert_called_once_with(scan_id, mock.ANY)

    assert instance.status(scan_id) == (0, None)

    assert instance.abort(scan_id)
    with pytest.raises(scanner.UknkownScanID):
        instance.status(scan_id)

    with pytest.raises(scanner.UknkownScanID):
        instance.abort(scan_id)

    instance.stop()
    asyncio.wait_for(run_task, 1)
    instance.cleanup()
    instance.session.close.assert_called_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize('train_found', [True, False])
@pytest.mark.parametrize('ct_letter,ct_found', [
    (None, True),
    ('К', True),
    ('Z', False)])
@pytest.mark.parametrize('booked', [True, False])
async def test_scan(train_found, ct_letter, ct_found, booked, train,
                    source_station, destination_station):
    success_cb_id = 'id123'
    firstname = 'firstname'
    lastname = 'lastname'
    date = datetime(2016, 1, 1)
    train_num = '741K'

    session_id = 'ssid'

    success_cb = mock.Mock(return_value=Awaitable())
    instance = scanner.UZScanner(success_cb, 1)
    instance.client = mock.Mock()
    instance.client.fetch_train.return_value = Awaitable(train if train_found else None)
    instance.book = mock.Mock()
    instance.book.return_value = Awaitable(session_id if booked else None)

    asyncio.ensure_future(instance.run())

    scan_id = instance.add_item(
        success_cb_id, firstname, lastname, date, source_station, destination_station,
        train_num, ct_letter)
    await asyncio.sleep(0.01)

    instance.client.fetch_train.assert_called_once_with(
        date, source_station, destination_station, train_num)
    if not train_found:
        assert instance.status(scan_id) == (1, 'Train 741K not found')
    elif not ct_found:
        assert instance.status(scan_id) == (1, 'Coach type {} not found'.format(ct_letter))
    else:
        coach_types = train.coach_types if ct_letter is None else [train.coach_types[-1]]

        instance.book.assert_called_once_with(
            train, coach_types, firstname, lastname)
        if booked:
            success_cb.assert_called_once_with(success_cb_id, session_id)
        else:
            assert instance.status(scan_id) == (1, 'No available seats')
    instance.stop()
    instance.cleanup()
