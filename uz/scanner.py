import asyncio
import logging
from uuid import uuid4

import aiohttp

from uz.client import UZClient
from uz.client.exceptions import ResponseError
from uz.metrics import statsd
from uz.utils import reliable_async_sleep


logger = logging.getLogger('uz.scanner')


class UZScanner(object):

    metric_sample_rate = 5

    def __init__(self, success_cb, delay=60):
        self.success_cb = success_cb

        self.loop = asyncio.get_event_loop()
        self.delay = delay
        self.session = aiohttp.ClientSession()
        self.client = UZClient(self.session)
        self.__state = dict()
        self.__running = False

    async def run(self):
        logger.info('Starting UZScanner')
        self.__running = True
        asyncio.ensure_future(self.emit_stats())
        while self.__running:
            for scan_id, data in self.__state.items():
                asyncio.ensure_future(self.scan(scan_id, data))
            await reliable_async_sleep(self.delay)

    def stop(self):
        logger.info('Stopping UZScanner')
        self.__running = False

    def cleanup(self):
        self.session.close()

    async def emit_stats(self):
        while self.__running:
            cnt = len(self.__state)
            statsd.gauge('scanner.active_scans', cnt)
            await asyncio.sleep(self.metric_sample_rate)

    def add_item(self, success_cb_id, firstname, lastname, date,
                 source, destination, train_num, ct_letter=None):
        scan_id = uuid4().hex
        self.__state[scan_id] = dict(
            success_cb_id=success_cb_id,
            firstname=firstname,
            lastname=lastname,
            date=date,
            source=source,
            destination=destination,
            train_num=train_num,
            ct_letter=ct_letter,
            lock=asyncio.Lock(),
            attempts=0,
            error=None)
        return scan_id

    def status(self, scan_id):
        # TODO: add protection. status requests should be limited to scans for current user only
        data = self.__state.get(scan_id)
        if data is None:
            raise UknkownScanID(scan_id)
        return data['attempts'], data['error']

    def abort(self, scan_id):
        if scan_id in self.__state:
            del self.__state[scan_id]
            return True
        raise UknkownScanID(scan_id)

    @staticmethod
    def handle_error(scan_id, data, error):
        data['error'] = error
        logger.debug('[%s] %s', scan_id, error)

    @staticmethod
    def find_coach_type(train, ct_letter):
        for coach_type in train.coach_types:
            if coach_type.letter == ct_letter:
                return coach_type

    @staticmethod
    async def book(train, source, destination, coach_types, firstname, lastname):
        with UZClient() as client:
            for coach_type in coach_types:
                for coach in await client.list_coaches(train, source, destination, coach_type):
                    try:
                        seats = await client.list_seats(train, source, destination, coach)
                    except ResponseError:
                        continue
                    for seat in seats:
                        try:
                            await client.book_seat(train, source, destination, coach, seat, firstname, lastname)
                        except ResponseError:
                            continue
                        return client.get_session_id()

    async def scan(self, scan_id, data):
        if data['lock'].locked():
            return

        async with data['lock']:
            data['attempts'] += 1

            train = await self.client.fetch_train(
                data['date'], data['source'], data['destination'], data['train_num'])
            if train is None:
                return self.handle_error(
                    scan_id, data, 'Train {} not found'.format(data['train_num']))

            if data['ct_letter']:
                coach_type = self.find_coach_type(train, data['ct_letter'])
                if coach_type is None:
                    return self.handle_error(
                        scan_id, data, 'Coach type {} not found'.format(data['ct_letter']))
                coach_types = [coach_type]
            else:
                coach_types = train.coach_types

            session_id = await self.book(train, data['source'], data['destination'], coach_types, data['firstname'], data['lastname'])
            if session_id is None:
                return self.handle_error(scan_id, data, 'No available seats')

            await self.success_cb(data['success_cb_id'], session_id)
            self.abort(scan_id)


class UknkownScanID(Exception):
    pass
