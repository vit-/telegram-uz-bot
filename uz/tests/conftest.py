import pytest

from uz.tests import read_file

from uz.client import model
from uz import utils


@pytest.fixture
def train_raw():
    return {
        'category': 1,
        'from': {'date': 1463368920,
                 'src_date': '2016-05-16 06:22:00',
                 'station': 'Darnytsya',
                 'station_id': '2200007'},
        'model': 1,
        'num': '741К',
        'till': {'date': 1463389200,
                 'src_date': '2016-05-16 12:00:00',
                 'station': 'Truskavets',
                 'station_id': '2218000'},
        'travel_time': '5:38',
        'types': [{'letter': 'С1',
                   'places': 123, 'title':
                   'Seating first class'},
                  {'letter': 'С2',
                   'places': 257,
                   'title': 'Seating second class'}]}


@pytest.fixture
def station_raw():
    return {'station_id': 2200007, 'title': 'Darnytsya'}


@pytest.fixture
def another_station_raw():
    return {'station_id': 2200001, 'title': 'Kyiv'}


@pytest.fixture
def coach_type_raw():
    return {
        'letter': 'С1',
        'places': 123, 'title':
        'Seating first class'}


@pytest.fixture
def coach_raw():
    return {
        'allow_bonus': False,
        'coach_class': '2',
        'coach_type_id': 21,
        'hasBedding': False,
        'num': 3,
        'places_cnt': 54,
        'prices': {'А': 31021},
        'reserve_price': 1700,
        'services': []}


@pytest.fixture
def seats_raw():
    return {
        'css': 'kr t19',
        'places': {'А': ['6', '9', '10', '14', '16', '18']}}


@pytest.fixture
def uz_timestamp():
    return {'date': 1463368920, 'src_date': '2016-05-16 06:22:00'}


@pytest.fixture
def source_station():
    return model.Station(2200001, 'Kyiv')


@pytest.fixture
def destination_station():
    return model.Station(2218000, 'Lviv')


@pytest.fixture
def coach_type():
    return model.CoachType('К', 51, 'Coupe / coach with compartments')


@pytest.fixture
def train():
    return model.Train(
        0, 0, '091К', '7:25',
        [model.CoachType('Л', 18, 'Suite / first-class sleeper'),
         model.CoachType('К', 51, 'Coupe / coach with compartments')],
        model.Station('2200001', 'Kyiv-Pasazhyrsky'),
        model.Station('2218000', 'Lviv'),
        model.UZTimestamp(1466451660, '2016-06-20 22:41:00'),
        model.UZTimestamp(1466478360, '2016-06-21 06:06:00'))


@pytest.fixture
def coach():
    return model.Coach(False, 'Б', 3, True, 8, 10, {'А': 33850}, 1700, ['Ч', 'Ш'])


@pytest.fixture
def index_page():
    return read_file('fixtures/index.html')


@pytest.yield_fixture
def patch_sleep_resolution():
    orig = utils.RESOLUTION
    utils.RESOLUTION = 0.1
    yield
    utils.RESOLUTION = orig
