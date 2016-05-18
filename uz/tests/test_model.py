import pytest

from uz.model import Train, CoachType, Coach, Station, UZTimestamp


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
def uz_timestamp():
    return {'date': 1463368920, 'src_date': '2016-05-16 06:22:00'}


def assert_model(klass, dikt):
    instance = klass.from_dict(dikt)
    assert instance.to_dict() == dikt
    exec('assert %r.to_dict() == %r' % (instance, dikt))
    assert instance == klass.from_dict(dikt)
    assert str(instance)
    return instance


def test_train(train_raw):
    train = assert_model(Train, train_raw)
    assert train.info()


def test_station(station_raw):
    assert_model(Station, station_raw)


def test_coach_type(coach_type_raw):
    assert_model(CoachType, coach_type_raw)


def test_coach(coach_raw):
    assert_model(Coach, coach_raw)


def test_uz_timestamp(uz_timestamp):
    assert_model(UZTimestamp, uz_timestamp)
