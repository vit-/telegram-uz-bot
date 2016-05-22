from uz.model import Train, CoachType, Coach, Station, UZTimestamp


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
