import asyncio

import mock
import pytest

from uz import client


class AIOMock(mock.MagicMock):

    def __aenter__(self):
        return self

    def __aexit__(self, exc_type, exc_value, traceback):
        return

    def __await__(self):
        yield from asyncio.sleep(0)
        return self


class Awaitable(object):

    def __init__(self, value):
        self.value = value

    def __await__(self):
        yield from asyncio.sleep(0)
        return self.value


def http_response(status, body):
    response = AIOMock()
    response.status = status
    response.read.return_value = Awaitable(str(body))
    response.json.return_value = Awaitable(body)
    return response


class TestUZClient(object):

    base_url = 'http://booking.uz.gov.ua/en'

    def uri(self, endpoint):
        return '{}/{}'.format(self.base_url, endpoint)

    def test_no_session(self):
        with pytest.raises(client.ImproperlyConfigured):
            client.UZClient().session

    def test_session_ok(self):
        session = 'session'
        assert client.UZClient(session).session == session

    @pytest.mark.asyncio
    @pytest.mark.parametrize('status,body,ex', [
        (400, 'body', client.BadRequest),
        (404, 'body', client.HTTPError),
        (200, {'error': True}, client.ResponseError)])
    async def test_call_raise(self, status, body, ex):
        session = AIOMock()
        session.request.return_value = http_response(status, body)
        endpoint = 'i/am/endpoint'

        uz = client.UZClient(session)

        with pytest.raises(ex):
            with mock.patch.object(uz, '_is_token_outdated',
                                   return_value=False):
                await uz.call(endpoint)

        session.request.assert_called_once_with('POST', self.uri(endpoint))
