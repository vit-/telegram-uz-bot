from dateutil import parser as date_parser


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
