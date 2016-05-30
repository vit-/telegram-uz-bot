import os

from uz.client import UZClient
from uz.interface.serializer import Deserializer, SerializerException
from uz.interface.telegram import bot
from uz.metrics import count_hits
from uz.scanner import UknkownScanID


SCAN_DALAY_SEC = int(os.environ.get('SCAN_DALAY_SEC') or 10)
TOKEN = os.environ.get('TG_BOT_TOKEN')
BOT_NAME = os.environ.get('TG_BOT_NAME')


if TOKEN:
    tg_bot = bot.UZTGBot(api_token=TOKEN, name=BOT_NAME, api_timeout=SCAN_DALAY_SEC)
else:
    print('TG_BOT_TOKEN env var is not specified, using StdOutBot')
    tg_bot = bot.StdOutBot(api_token=None)


@tg_bot.command(r'/trains (?P<date>[\w.\-]+) (?P<source>\w+) (?P<destination>\w+)')
@count_hits('interface.telegram.command.trains')
async def list_trains(chat, match):
    with UZClient() as uz:
        try:
            date, source, destination = await Deserializer(uz).load(match.groupdict())
        except SerializerException as ex:
            return await chat.send_text(str(ex))

        trains = await uz.list_trains(date, source, destination)
    msg = 'Trains from %s to %s on %s:\n\n' % (
        source, destination, date.date())
    for train in trains:
        msg += '%s\n==========\n\n' % train.info()
    return await chat.send_text(msg)


@tg_bot.command(r'/status (?P<scan_id>.+)')
@count_hits('interface.telegram.command.status')
async def status(chat, match):
    scan_id = match.groupdict()['scan_id']
    try:
        attempts, error = chat.bot.scanner.status(scan_id)
    except UknkownScanID:
        return await chat.send_text('Unknown scan id: {}'.format(scan_id))
    msg = 'No attempts: {}\nLast error message: {}'.format(attempts, error)
    return await chat.send_text(msg)


@tg_bot.command(r'/abort (?P<scan_id>.+)')
@count_hits('interface.telegram.command.abort_scan')
async def abort_scan(chat, match):
    scan_id = match.groupdict()['scan_id']
    try:
        chat.bot.scanner.abort(scan_id)
    except UknkownScanID:
        return await chat.send_text('Unknown scan id: {}'.format(scan_id))
    return await chat.send_text('OK')


@tg_bot.command(r'/scan (?P<date>[\w.\-]+) (?P<source>\w+) (?P<destination>\w+) (?P<train_num>\w+)( (?P<ct_letter>\w+))?')  # noqa
@count_hits('interface.telegram.command.scan')
async def scan(chat, match):
    raw_data = match.groupdict()
    with UZClient() as uz:
        try:
            date, source, destination = await Deserializer(uz).load(raw_data)
        except SerializerException as ex:
            return await chat.send_text(str(ex))

    train_num = raw_data['train_num']
    ct_letter = raw_data['ct_letter']

    scan_id = await chat.bot.scanner.add_item(
        chat.message, 'Firstname', 'Lastname', date, source, destination, train_num, ct_letter)
    msg = ('Scanning tickets for train {} from {} to {} on {}.\n'
           'To monitor scan status use command:\n'
           '/status {}').format(
        train_num, source, destination, date.date(), scan_id)
    return await chat.send_text(msg)


@tg_bot.command(r'/help')
@count_hits('interface.telegram.command.help')
async def help_msg(chat, match):
    return await chat.send_text('Help is on it\'s way!')


@tg_bot.default
@count_hits('interface.telegram.command.hello')
async def hello(chat, message):
    if message.get('text'):
        return await chat.send_text('Hello! I am UZ Tickets Bot! Use /help to see what I can')
