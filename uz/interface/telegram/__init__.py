import os

from uz.client import UZClient
from uz.interface.serializer import Deserializer, SerializerException
from uz.interface.telegram.bot import UZTGBot
from uz.interface.telegram.dev_bot import StdOutBot
from uz.metrics import count_hits
from uz.scanner import UknkownScanID


SCAN_DALAY_SEC = int(os.environ.get('SCAN_DALAY_SEC') or 10)
TOKEN = os.environ.get('TG_BOT_TOKEN')
BOT_NAME = os.environ.get('TG_BOT_NAME')


if TOKEN:
    bot = UZTGBot(api_token=TOKEN, name=BOT_NAME, api_timeout=SCAN_DALAY_SEC)
else:
    print('TG_BOT_TOKEN env var is not specified, using StdOutBot')
    bot = StdOutBot(api_token=None)


@bot.command(r'/trains (?P<date>[\w.\-]+) (?P<source>\w+) (?P<destination>\w+)')
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


@bot.command(r'/status_(?P<scan_id>.+)')
@count_hits('interface.telegram.command.status')
async def status(chat, match):
    scan_id = match.groupdict()['scan_id']
    try:
        attempts, error = chat.bot.scanner.status(scan_id)
    except UknkownScanID:
        return await chat.send_text('Unknown scan id: {}'.format(scan_id))
    msg = 'No attempts: {}\nLast error message: {}'.format(attempts, error)
    return await chat.send_text(msg)


@bot.command(r'/abort_(?P<scan_id>.+)')
@count_hits('interface.telegram.command.abort_scan')
async def abort_scan(chat, match):
    scan_id = match.groupdict()['scan_id']
    try:
        chat.bot.scanner.abort(scan_id)
    except UknkownScanID:
        return await chat.send_text('Unknown scan id: {}'.format(scan_id))
    return await chat.send_text('OK')


@bot.command(r'/scan (?P<firstname>\w+) (?P<lastname>\w+) (?P<date>[\w.\-]+) (?P<source>\w+) (?P<destination>\w+) (?P<train_num>\w+)( (?P<ct_letter>\w+))?')  # noqa
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
    firstname = raw_data['firstname']
    lastname = raw_data['lastname']

    scan_id = chat.bot.scanner.add_item(
        chat.message, firstname, lastname, date, source, destination, train_num, ct_letter)
    msg = ('Scanning tickets for train {train} from {src} to {dst} on {date}.\n'
           'To monitor scan status: /status_{sid}\n'
           'To abort scan: /abort_{sid}').format(
        train=train_num,
        src=source,
        dst=destination,
        date=date.date(),
        sid=scan_id)
    return await chat.send_text(msg)


@bot.command(r'/help')
@count_hits('interface.telegram.command.help')
async def help_msg(chat, match):
    return await chat.send_text(
        'Use /trains to list available trains for a specific date and route. '
        'For example:\n'
        '/trains 2016-01-01 Kyiv Lviv\n\n'
        'Use /scan to initiate tickets monitoring. For example:\n'
        '/scan Firstname Lastname 2016-01-01 Kyiv Lviv 743K\n'
        'You can optionally provide a coach type you prefer:\n'
        '/scan Firstname Lastname 2016-01-01 Kyiv Lviv 743K C2\n\n'
        'Once the ticket is booked you need to proceed to checkout in your browser '
        'using a provided Session ID.'
    )


@bot.default
@count_hits('interface.telegram.command.hello')
async def hello(chat, message):
    if message.get('text'):
        return await chat.send_text(
            'Hello! I am UZ Tickets Bot!\n'
            'I am here to help you in buying UZ railway tickets on a highly loaded trains.\n'
            'Type /help to get a list of commands.'
        )
