import time
from datetime import datetime

import mock
import pytest

from uz.tests import Awaitable

from uz.interface.telegram import bot
from uz.scanner import UknkownScanID


CHAT_ID = 'chat_id'


def tg_message(text):
    return {
        'chat': {
            'id': CHAT_ID,
            'type': 'private',
        },
        'from': {'first_name': 'n/a', 'id': 'user_id'},
        'message_id': int(time.time()),
        'text': text
    }


def get_reply(send_message_mock):
    args, kwargs = send_message_mock.call_args_list[0]
    return args[1]


@pytest.mark.asyncio
async def test_list_trains(source_station, destination_station, train):
    bot.send_message = send_message = mock.MagicMock(return_value=Awaitable())
    date = datetime(2016, 7, 21)
    command = '/trains {} {} {}'.format(
        date.strftime('%Y-%m-%d'), source_station.title, destination_station.title)
    with mock.patch('uz.interface.serializer.Deserializer.load',
                    return_value=Awaitable((date, source_station, destination_station))) as load, \
            mock.patch('uz.client.client.UZClient.list_trains',
                       return_value=Awaitable([train])) as list_trains:
        await bot._process_message(tg_message(command))
    load.assert_called_once_with({
        'date': date.strftime('%Y-%m-%d'),
        'source': source_station.title,
        'destination': destination_station.title})
    list_trains.assert_called_once_with(date, source_station, destination_station)
    msg = get_reply(send_message)
    title = 'Trains from %s to %s on %s:' % (
        source_station, destination_station, date.date())
    assert msg.startswith(title)
    assert train.info() in msg


@pytest.mark.asyncio
@pytest.mark.parametrize('is_ok', [True, False])
async def test_status(is_ok):
    scan_id = 'id1234'
    scanner = mock.MagicMock()
    if is_ok:
        scanner.status.return_value = (attempts, error) = (10, 'i am error')
    else:
        scanner.status.side_effect = UknkownScanID()
    bot.send_message = send_message = mock.MagicMock(return_value=Awaitable())
    bot.set_scanner(scanner)
    await bot._process_message(tg_message('/status_{}'.format(scan_id)))
    scanner.status.assert_called_once_with(scan_id)
    if is_ok:
        send_message.assert_called_once_with(
            CHAT_ID, 'No attempts: {}\nLast error message: {}'.format(attempts, error))
    else:
        send_message.assert_called_once_with(
            CHAT_ID, 'Unknown scan id: {}'.format(scan_id))


@pytest.mark.asyncio
@pytest.mark.parametrize('is_ok', [True, False])
async def test_abort_scan(is_ok):
    scan_id = 'id4321'
    scanner = mock.MagicMock()
    if is_ok:
        scanner.abort.return_value = True
    else:
        scanner.abort.side_effect = UknkownScanID()
    bot.send_message = send_message = mock.MagicMock(return_value=Awaitable())
    bot.set_scanner(scanner)
    await bot._process_message(tg_message('/abort_{}'.format(scan_id)))
    scanner.abort.assert_called_once_with(scan_id)
    if is_ok:
        send_message.assert_called_once_with(
            CHAT_ID, 'OK')
    else:
        send_message.assert_called_once_with(
            CHAT_ID, 'Unknown scan id: {}'.format(scan_id))


@pytest.mark.asyncio
@pytest.mark.parametrize('ct_letter', [None, 'C2'])
async def test_scan(source_station, destination_station, ct_letter):
    scan_id = 'id1234'
    date = datetime(2016, 10, 7)
    train_num = '744K'
    firstname = 'username'
    lastname = 'surname'
    parts = [
        '/scan',
        firstname,
        lastname,
        date.strftime('%Y-%m-%d'),
        source_station,
        destination_station,
        train_num]
    if ct_letter:
        parts.append(ct_letter)
    command = ' '.join(str(i) for i in parts)

    scanner = mock.MagicMock()
    scanner.add_item.return_value = Awaitable(scan_id)
    bot.send_message = send_message = mock.MagicMock(return_value=Awaitable())
    bot.set_scanner(scanner)

    with mock.patch('uz.interface.serializer.Deserializer.load',
                    return_value=Awaitable((date, source_station, destination_station))) as load:
        await bot._process_message(tg_message(command))
    load.assert_called_once_with({
        'firstname': firstname,
        'lastname': lastname,
        'date': date.strftime('%Y-%m-%d'),
        'source': source_station.title,
        'destination': destination_station.title,
        'train_num': train_num,
        'ct_letter': ct_letter})
    scanner.add_item.assert_called_once_with(
        mock.ANY, firstname, lastname, date, source_station, destination_station,
        train_num, ct_letter)
    expected = ('Scanning tickets for train {train} from {src} to {dst} on {date}.\n'
                'To monitor scan status: /status_{sid}\n'
                'To abort scan: /abort_{sid}').format(
        train=train_num,
        src=source_station,
        dst=destination_station,
        date=date.date(),
        sid=scan_id)
    send_message.assert_called_once_with(CHAT_ID, expected)


@pytest.mark.asyncio
async def test_hello():
    bot.send_message = send_message = mock.MagicMock(return_value=Awaitable())
    await bot._process_message(tg_message('hi'))
    send_message.assert_called_once_with(CHAT_ID, mock.ANY)


@pytest.mark.asyncio
async def test_help_msg():
    bot.send_message = send_message = mock.MagicMock(return_value=Awaitable())
    await bot._process_message(tg_message('/help'))
    send_message.assert_called_once_with(CHAT_ID, mock.ANY)
