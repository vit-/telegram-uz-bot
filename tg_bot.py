import asyncio
import logging
import os
import sys

import aiotg

from dateutil import parser as date_parser

from uz.client import UZClient
from uz.scanner import UZScanner, UknkownScanID

TIMEOUT = 10
TOKEN = os.environ.get('TG_BOT_TOKEN')
assert TOKEN, 'TG_BOT_TOKEN env var is not specified'


def ticket_booked_cb(orig_msg, session_id):
    chat = aiotg.Chat.from_message(bot, orig_msg)
    msg = ('Ticket is booked! To proceed checkout use this session id '
           'in your browser: {}'.format(session_id))
    return chat.send_text(msg)


bot = aiotg.Bot(api_token=TOKEN, name='uz_ticket_bot', api_timeout=TIMEOUT)
scanner = UZScanner(ticket_booked_cb, timeout=TIMEOUT)


class SerializerException(Exception):
    pass


class Deserializer(object):

    def __init__(self, client):
        self.client = client

    async def load(self, dikt):
        date = self.date(dikt['date'])
        source_coro = self.station(dikt['source'])
        destination_coro = self.station(dikt['destination'])
        return date, await source_coro, await destination_coro

    @staticmethod
    def date(date_str):
        if not date_str:
            return
        try:
            return date_parser.parse(date_str)
        except ValueError as ex:
            raise SerializerException(ex)

    async def station(self, name):
        if not name:
            return
        return await self.client.fetch_first_station(name)


@bot.command(r'/trains (?P<date>[\w.]+) (?P<source>\w+) (?P<destination>\w+)')
async def list_trains(chat, match):
    with UZClient() as uz:
        date, source, destination = await Deserializer(uz).load(
            match.groupdict())

        trains = await uz.list_trains(date, source, destination)
        msg = 'Trains from %s to %s on %s:\n\n' % (
            source, destination, date.date())
        for train in trains:
            msg += '%s\n==========\n\n' % train.info()
        return await chat.send_text(msg)


@bot.command(r'/status (?P<scan_id>.+)')
async def status(chat, match):
    scan_id = match.groupdict()['scan_id']
    try:
        attempts, error = scanner.status(scan_id)
    except UknkownScanID:
        return await chat.send_text('Unknown scan id: {}'.format(scan_id))
    msg = 'No attempts: {}\nLast error message: {}'.format(attempts, error)
    return await chat.send_text(msg)


@bot.command(r'/stop_scan (?P<scan_id>.+)')
async def stop_scan(chat, match):
    scan_id = match.groupdict()['scan_id']
    return scanner.stop_scan(scan_id)


@bot.command(r'/scan (?P<date>[\w.]+) (?P<source>\w+) (?P<destination>\w+) (?P<train_num>\w+)( (?P<ct_letter>\w+))?')  # noqa
async def scan(chat, match):
    with UZClient() as uz:
        raw_data = match.groupdict()
        date, source, destination = await Deserializer(uz).load(raw_data)
        train_num = raw_data['train_num']
        ct_letter = raw_data['ct_letter']

        scan_id = await scanner.add_item(
            chat.message, 'Firstname', 'Lastname', date, source, destination,
            train_num, ct_letter)
        msg = ('Scanning tickets for train {} from {} to {} on {}.\n'
               'To monitor scan status use command:\n'
               '/status {}').format(
            train_num, source, destination, date.date(), scan_id)
        return await chat.send_text(msg)


def configure_logging():
    level = logging.DEBUG
    loggers = [
        # 'aiotg',
        'uz.client',
        'uz.scanner',
    ]
    for i in loggers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(level)

        log = logging.getLogger(i)
        log.setLevel(level)
        log.addHandler(handler)


if __name__ == '__main__':
    configure_logging()
    loop = asyncio.get_event_loop()
    loop.create_task(bot.loop())
    print('Running...')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Shutting down...')
        print('Waiting for all tasks to complete...')
        bot.stop()
        scanner.stop()
        pending = asyncio.Task.all_tasks()
        loop.run_until_complete(asyncio.gather(*pending))
        scanner.cleanup()
        loop.stop()
