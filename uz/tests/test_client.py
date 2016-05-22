import asyncio
from datetime import datetime

import mock
import pytest

from uz import client, model


class AIOMock(mock.MagicMock):

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return


class Awaitable(object):

    def __init__(self, value):
        self.value = value

    def __await__(self):
        yield from asyncio.sleep(0)
        return self.value


def http_response(body, status=200):
    response = AIOMock()
    response.status = status
    response.read.return_value = Awaitable(str(body).encode('utf-8'))
    response.json.return_value = Awaitable(body)
    return response


class TestUZClient(object):

    base_url = 'http://booking.uz.gov.ua/en'

    def get_headers(self):
        return {
            'GV-Ajax': '1',
            'GV-Referer': self.base_url,
            'GV-Token': None
        }

    def uri(self, endpoint):
        return '{}/{}'.format(self.base_url, endpoint)

    @staticmethod
    def get_client(response_mock=None):
        session = AIOMock()
        if response_mock:
            session.request.return_value = response_mock
        uz = client.UZClient(session)
        # _is_token_outdated == False
        uz._token_date = 9999999999
        return uz

    def assert_request_call(self, uz, endpoint, **kw):
        uz.session.request.assert_called_once_with(
            'POST', self.uri(endpoint), headers=self.get_headers(), **kw)

    def test_no_session(self):
        with pytest.raises(client.ImproperlyConfigured):
            client.UZClient().session

    def test_session_ok(self):
        session = 'session'
        assert client.UZClient(session).session == session

    @pytest.mark.asyncio
    async def test_get_token(self, index_page):
        expected = '33107f87dadad37307f93da538b73138'

        uz = self.get_client(http_response(index_page))
        uz._token_date = 0  # reset mocked value from previous call

        result = await uz.get_token()

        assert result == expected
        assert uz._token == expected
        assert uz._token_date

        uz.session.request.assert_called_once_with('POST', self.uri(''), headers=None)

    @pytest.mark.asyncio
    async def test_get_token_fail(self):
        uz = self.get_client(http_response(''))
        uz._token_date = 0  # reset mocked value from previous call

        with pytest.raises(client.FailedObtainToken):
            await uz.get_token()

    @pytest.mark.asyncio
    @pytest.mark.parametrize('status,body,ex', [
        (400, 'body', client.BadRequest),
        (404, 'body', client.HTTPError),
        (200, {'error': True}, client.ResponseError)])
    async def test_call_raise(self, status, body, ex):
        endpoint = 'i/am/endpoint'

        uz = self.get_client(http_response(body, status))
        with pytest.raises(ex):
            await uz.call(endpoint)

        uz.session.request.assert_called_once_with(
            'POST', self.uri(endpoint), headers=self.get_headers())

    @pytest.mark.asyncio
    @pytest.mark.parametrize('is_raw', [True, False])
    async def test_call_ok(self, is_raw):
        body = {'hello': 'world'}
        expected = str(body).encode('utf-8') if is_raw else body
        endpoint = 'i/am/endpoint/ok'

        uz = self.get_client(http_response(body))
        result = await uz.call(endpoint, method='GET', raw=is_raw)

        assert result == expected
        uz.session.request.assert_called_once_with(
            'GET', self.uri(endpoint), headers=self.get_headers())

    @pytest.mark.asyncio
    async def test_search_stations(self, station_raw):
        name = 'lviv'
        endpoint = 'purchase/station/{}/'.format(name)
        response = {'value': [station_raw, station_raw]}
        expected = [model.Station.from_dict(station_raw) for _ in range(2)]

        uz = self.get_client(http_response(response))
        result = await uz.search_stations(name)

        assert result == expected
        self.assert_request_call(uz, endpoint)

    @pytest.mark.asyncio
    @pytest.mark.parametrize('is_found', [True, False])
    async def test_fetch_first_station(self, is_found, station_raw):
        name = 'lviv'
        endpoint = 'purchase/station/{}/'.format(name)

        if is_found:
            response = {'value': [station_raw]}
            expected = model.Station.from_dict(station_raw)
        else:
            response = {'value': []}
            expected = None

        uz = self.get_client(http_response(response))
        result = await uz.fetch_first_station(name)

        assert result == expected
        self.assert_request_call(uz, endpoint)

    @pytest.mark.asyncio
    async def test_list_trains(self, source_station, destination_station, train_raw):
        date = datetime(2016, 7, 1)
        data = dict(
            station_id_from=source_station.id,
            station_id_till=destination_station.id,
            date_dep='07.01.2016',
            time_dep='00:00',
            time_dep_till='',
            another_ec=0,
            search='')

        response = {'value': [train_raw, train_raw]}
        expected = [model.Train.from_dict(train_raw) for _ in range(2)]

        uz = self.get_client(http_response(response))
        result = await uz.list_trains(date, source_station, destination_station)

        assert result == expected
        self.assert_request_call(uz, 'purchase/search/', data=data)

    @pytest.mark.asyncio
    async def test_list_coaches(self, train, coach_type, coach_raw):
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
        response = {'value': {'coaches': [coach_raw, coach_raw]}}
        expected = [model.Coach.from_dict(coach_raw) for _ in range(2)]

        uz = self.get_client(http_response(response))
        result = await uz.list_coaches(train, coach_type)

        assert result == expected
        self.assert_request_call(uz, 'purchase/coaches/', data=data)

    @pytest.mark.asyncio
    async def test_list_seats(self, train, coach, seats_raw):
        data = dict(
            station_id_from=train.source_station.id,
            station_id_till=train.destination_station.id,
            train=train.num,
            coach_num=coach.num,
            coach_class=coach.klass,
            coach_type_id=coach.type_id,
            date_dep=train.departure_time.timestamp
        )
        response = {'value': seats_raw}
        expected = {'6', '9', '10', '14', '16', '18'}

        uz = self.get_client(http_response(response))
        result = await uz.list_seats(train, coach)

        assert result == expected
        self.assert_request_call(uz, 'purchase/coach/', data=data)

    @pytest.mark.asyncio
    async def test_book_seat(self, train, coach):
        seat = '19'
        firstname = 'Name'
        lastname = 'Surname'
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

        expected = response = {'error': False}

        uz = self.get_client(http_response(response))
        result = await uz.book_seat(train, coach, seat, firstname, lastname)

        assert result == expected
        self.assert_request_call(uz, 'cart/add/', data=data)


@mock.patch('aiohttp.ClientSession')
def test_client_context_manager(client_session):
    with client.UZClient() as uz:
        client_session.assert_called_once_with()
        assert uz.session == client_session.return_value
        assert not client_session.return_value.close.called
    client_session.return_value.close.assert_called_once_with()
