import asyncio
import logging
import os
import sys

from uz.interface.telegram import tg_bot
from uz.metrics import statsd
from uz.scanner import UZScanner


logger = logging.getLogger('main')
DEFAULT_LEVEL = logging.WARNING

SCAN_DALAY_SEC = int(os.environ.get('SCAN_DALAY_SEC') or 10)


def get_log_level():
    level = logging.getLevelName(os.environ.get('LOG_LEVEL', '').upper())
    if not isinstance(level, int):
        level = DEFAULT_LEVEL
    return level


def configure_logging(level=None):
    level = level or get_log_level()
    loggers = [
        'main',
        'uz.client',
        'uz.metrics',
        'uz.scanner',
    ]
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    for i in loggers:
        log = logging.getLogger(i)
        log.setLevel(level)
        log.addHandler(handler)


def init_statsd():
    host = os.environ.get('STATSD_HOST')
    port = os.environ.get('STATSD_PORT')
    if host and port:
        statsd.host = host
        statsd.port = int(port)


if __name__ == '__main__':
    configure_logging()
    init_statsd()

    scanner = UZScanner(tg_bot.ticket_booked_cb, SCAN_DALAY_SEC)
    tg_bot.set_scanner(scanner)
    loop = asyncio.get_event_loop()
    loop.create_task(tg_bot.loop())
    loop.create_task(scanner.run())
    logger.warning('Running...')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        tg_bot.stop()
        scanner.stop()
        logger.warning('Shutting down...')
        logger.warning('Waiting for all tasks to complete...')
        pending = asyncio.Task.all_tasks()
        loop.run_until_complete(asyncio.gather(*pending))
        scanner.cleanup()
        loop.stop()
