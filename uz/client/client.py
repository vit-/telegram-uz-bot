import asyncio
import logging
import time
from itertools import chain

import aiohttp

from uz.client.exceptions import (
    FailedObtainToken, HTTPError, BadRequest, ResponseError, ImproperlyConfigured)
from uz.client.model import DATE_FMT, Train, Station, Coach
from uz.client.utils import parse_gv_token, get_random_user_agent


logger = logging.getLogger('uz.client')


class UZClient(object):

    base_url = 'http://booking.uz.gov.ua/en'

    def __init__(self, session=None, request_timeout=10):
        self._session = session
        self.request_timeout = request_timeout

        self._token_lock = asyncio.Lock()
        self._token = None
        self._token_date = 0
        self._token_max_age = 600  # 10 minutes
        self._user_agent = None

    def __enter__(self):
        self._session = aiohttp.ClientSession()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    @property
    def session(self):
        if self._session is None:
            raise ImproperlyConfigured('Session is not configured')
        return self._session

    @property
    def user_agent(self):
        if self._user_agent is None:
            self._user_agent = get_random_user_agent()
        return self._user_agent

    def _is_token_outdated(self):
        return (time.time() - self._token_date) > self._token_max_age

    async def get_token(self):
        if self._is_token_outdated():
            async with self._token_lock:
                if self._is_token_outdated():
                    self._user_agent = None
                    self.session.cookies.clear()
                    headers = {'User-Agent': self.user_agent}
                    page = await self.call('', raw=True, headers=headers)
                    page = page.decode('utf-8')
                    self._token = parse_gv_token(page)
                    if self._token is None:
                        raise FailedObtainToken(page)
                    self._token_date = time.time()
        return self._token

    async def get_headers(self):
        return {
            'User-Agent': self.user_agent,
            'GV-Ajax': '1',
            'GV-Referer': self.base_url,
            'GV-Token': await self.get_token()
        }

    def uri(self, endpoint):
        return '{}/{}'.format(self.base_url, endpoint)

    def get_session_id(self):
        sid = self.session.cookies.get('_gv_sessid')
        return sid and sid.value

    async def call(self, endpoint, method='POST', raw=False, *args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = await self.get_headers()

        uri = self.uri(endpoint)
        logger.debug('Fetching: %s', uri)
        logger.debug('Headers: %s', kwargs['headers'])
        logger.debug('Cookies: %s', self.session.cookies)

        with aiohttp.Timeout(self.request_timeout):
            async with self.session.request(
                    method, uri, *args, **kwargs) as response:
                body = await response.read()
                if not response.status == 200:
                    try:
                        json = await response.json()
                    except Exception:  # TODO: narrow exception
                        json = None
                    ex = BadRequest if response.status == 400 else HTTPError
                    raise ex(response.status, body, kwargs.get('data'), json)
                if raw:
                    return body
                json = await response.json()
                if json.get('error'):
                    raise ResponseError(response.status, body, kwargs.get('data'), json)
                return json

    async def search_stations(self, name):
        endpoint = 'purchase/station/{}/'.format(name)
        result = await self.call(endpoint)
        return [Station.from_dict(i) for i in result['value']]

    async def fetch_first_station(self, name):
        stations = await self.search_stations(name)
        return stations and stations[0] or None

    async def list_trains(self, date, source_station, destination_station):
        data = dict(
            station_id_from=source_station.id,
            station_id_till=destination_station.id,
            date_dep=date.strftime(DATE_FMT),
            time_dep='00:00',
            time_dep_till='',
            another_ec=0,
            search='')
        result = await self.call('purchase/search/', data=data)
        return [Train.from_dict(i) for i in result['value']]

    async def fetch_train(self, date, source_station, destination_station, train_num):
        trains = await self.list_trains(date, source_station, destination_station)
        for train in trains:
            if train.num == train_num:
                return train

    async def list_coaches(self, train, coach_type):
        data = dict(
            station_id_from=train.source_station.id,
            station_id_till=train.destination_station.id,
            train=train.num,
            model=train.model,
            date_dep=train.departure_time.timestamp,
            round_trip=0,
            another_ec=0,
            coach_type=coach_type.letter
        )
        result = await self.call('purchase/coaches/', data=data)
        return [Coach.from_dict(i) for i in result['coaches']]

    async def list_seats(self, train, coach):
        data = dict(
            station_id_from=train.source_station.id,
            station_id_till=train.destination_station.id,
            train=train.num,
            coach_num=coach.num,
            coach_class=coach.klass,
            coach_type_id=coach.type_id,
            date_dep=train.departure_time.timestamp
        )
        result = await self.call('purchase/coach/', data=data)
        return set(chain(*result['value']['places'].values()))

    async def book_seat(self, train, coach, seat, firstname, lastname):
        data = dict(
            code_station_from=train.source_station.id,
            code_station_to=train.destination_station.id,
            train=train.num,
            date=train.departure_time.timestamp,
            round_trip=0)

        place = dict(
            ord=0,
            coach_num=coach.num,
            coach_class=coach.klass,
            coach_type_id=coach.type_id,
            place_num=seat,
            firstname=firstname,
            lastname=lastname,
            bedding=0,
            child='',
            stud='',
            transp=0,
            reserve=0)
        for key, value in place.items():
            data['places[0][{}]'.format(key)] = value
        result = await self.call('cart/add/', data=data)
        return result
