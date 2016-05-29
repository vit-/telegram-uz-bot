from dateutil import parser as date_parser


class SerializerException(Exception):
    pass


class Deserializer(object):

    def __init__(self, client):
        self.client = client

    async def load(self, dikt):
        date = self.date(dikt.get('date'))
        source_coro = self.station(dikt.get('source'))
        destination_coro = self.station(dikt.get('destination'))
        return date, await source_coro, await destination_coro

    @staticmethod
    def date(date_str):
        if not date_str:
            return
        try:
            return date_parser.parse(date_str)
        except ValueError:
            raise SerializerException('Unknown date format. Please use 2016-01-01')

    async def station(self, name):
        if not name:
            return
        station = await self.client.fetch_first_station(name)
        if station is None:
            raise SerializerException('Station {} not found'.format(name))
        return station
