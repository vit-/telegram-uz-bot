from datetime import datetime

import mock
import pytest

from uz.tests import http_response, get_uz_client

from uz.client.model import Station
from uz.interface import serializer


@pytest.mark.asyncio
async def test_deserializer(station_raw, another_station_raw):
    uz = get_uz_client()
    uz.session.request.side_effect = (http_response({'value': [station_raw]}),
                                      http_response({'value': [another_station_raw]}))
    date = datetime(2016, 10, 21)

    result = await serializer.Deserializer(uz).load(dict(
        date=date.strftime('%Y-%m-%d'),
        source=station_raw['title'],
        destination=another_station_raw['title']))
    assert result == (date, Station.from_dict(station_raw), Station.from_dict(another_station_raw))
    calls = [mock.call('POST', uz.uri('purchase/station/{}/'.format(i['title'])), headers=mock.ANY)
             for i in (station_raw, another_station_raw)]
    assert uz.session.request.call_args_list == calls


@pytest.mark.asyncio
async def test_deserializer_empty():
    uz = get_uz_client()
    result = await serializer.Deserializer(uz).load(dict())
    assert result == (None, None, None)


@pytest.mark.asyncio
async def test_deserializer_bad_date():
    uz = get_uz_client()
    with pytest.raises(serializer.SerializerException):
        await serializer.Deserializer(uz).load(dict(date='bad format'))
