import asyncio
import os
import sys
import time
from asyncio.streams import StreamWriter, FlowControlMixin

import aiotg


# aio reader/writer:
# https://gist.github.com/nathan-hoad/8966377


class StdOutBot(aiotg.Bot):

    _encoding = 'utf-8'

    _reader = None

    async def get_reader(self):
        if self._reader is None:
            self._reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self._reader)
            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        return self._reader

    _writer = None

    async def get_writer(self):
        if self._writer is None:
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.connect_write_pipe(
                FlowControlMixin, os.fdopen(0, 'wb'))
            self._writer = StreamWriter(transport, protocol, None, loop)
        return self._writer

    async def write(self, text):
        if isinstance(text, str):
            text = text.encode(self._encoding)
        writer = await self.get_writer()
        writer.write(text)
        await writer.drain()

    async def read(self, prompt=''):
        await self.write(prompt)
        reader = await self.get_reader()
        line = await reader.readline()
        return line.decode(self._encoding).replace('\r', '').replace('\n', '')

    async def send_message(self, chat_id, text, **options):
        await self.write('{}\n'.format(text))

    async def api_call(self, method, **params):
        if method == 'getUpdates':
            text = await self.read('>>> ')
            message_id = int(time.time())
            return {
                'ok': True,
                'result': [{
                    'update_id': message_id,
                    'message': {
                        'chat': {
                            'id': 'chat_id',
                            'type': 'private',
                        },
                        'from': {'first_name': 'n/a', 'id': 'user_id'},
                        'message_id': message_id,
                        'text': text
                    }
                }]
            }
        else:
            raise Exception('Method not mocked: {}'.format(method))
