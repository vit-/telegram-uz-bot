import asyncio
import os

import mock


def read_file(path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, path)) as f:
        return f.read()


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
