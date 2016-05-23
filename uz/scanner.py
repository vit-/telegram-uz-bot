import asyncio
import logging
from uuid import uuid4

import aiohttp
from datadog import statsd

from uz.client import UZClient, ResponseError


logger = logging.getLogger(__name__)


class UZScanner(object):

    metric_sample_rate = 5

    def __init__(self, success_cb, timeout=60):
        self.success_cb = success_cb

        self.loop = asyncio.get_event_loop()
        self.timeout = timeout
        self.session = aiohttp.ClientSession()
        self.client = UZClient(self.session)
        self.__state = dict()
        self.__running = False

    def run(self):
        self.__running = True
        asyncio.ensure_future(self.emit_stats())

    def stop(self):
        self.__running = False

    def cleanup(self):
        self.session.close()

    async def emit_stats(self):
        while self.__running:
            cnt = len(self.__state)
            statsd.gauge('scanner.active_scans', cnt, sample_rate=self.metric_sample_rate)
            logger.debug('[statsd] scanner.active_scans, %s', cnt)
            await asyncio.sleep(self.metric_sample_rate)

    async def add_item(self, success_cb_id, firstname, lastname, date,
                       source, destination, train_num, ct_letter=None):
        if not self.__running:
            logger.warning('Adding item to not running scanner')

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
            attempts=0,
            error=None)
        asyncio.ensure_future(self.scan(scan_id))
        return scan_id

    def status(self, scan_id):
        data = self.__state.get(scan_id)
        if data is None:
            raise UknkownScanID(scan_id)
        return data['attempts'], data['error']

    def stop_scan(self, scan_id):
        if scan_id in self.__state:
            del self.__state[scan_id]

    async def scan(self, scan_id):
        while self.__running:
            data = self.__state.get(scan_id)
            if data is None:
                logger.info(
                    'Scan id {} is not in state anymore. Stopping scan'.format(
                        scan_id))
                return

            data['attempts'] += 1

            train = None
            for i in await self.client.list_trains(
                    data['date'], data['source'], data['destination']):
                if i.num == data['train_num']:
                    train = i
                    break
            if train is None:
                error = 'Train {} not found'.format(data['train_num'])
                data['error'] = error
                logger.debug('[{}] {}'.format(scan_id, error))
                await asyncio.sleep(self.timeout)
                continue

            if data['ct_letter']:
                ct = None
                for i in train.coach_types:
                    if i.letter == data['ct_letter']:
                        ct = i
                        break
                if ct is None:
                    error = 'Coach type {} not found'.format(data['ct_letter'])
                    data['error'] = error
                    logger.debug('[{}] {}'.format(scan_id, error))
                    await asyncio.sleep(self.timeout)
                    continue
                coach_types = [ct]
            else:
                coach_types = train.coach_types

            with UZClient() as personal_client:
                for ct in coach_types:
                    for coach in await self.client.list_coaches(train, ct):
                        try:
                            seats = await self.client.list_seats(train, coach)
                        except ResponseError:
                            continue
                        for seat in seats:
                            try:
                                await personal_client.book_seat(
                                    train, coach, seat,
                                    data['firstname'], data['lastname'])
                            except ResponseError:
                                continue
                            sid = personal_client.get_session_id()
                            await self.success_cb(data['success_cb_id'], sid)
                            self.stop_scan(scan_id)
                            return
            error = 'No available seats'
            data['error'] = error
            logger.debug('[{}] {}'.format(scan_id, error))
            await asyncio.sleep(self.timeout)


class UknkownScanID(Exception):
    pass
