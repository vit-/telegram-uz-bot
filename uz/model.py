from datetime import datetime


DATE_FMT = '%m.%d.%Y'


class Train(object):

    def __init__(self, category, model, num, travel_time, coach_types,
                 source_station, destination_station, departure_time,
                 arrival_time):
        self.category = category
        self.model = model
        self.num = num
        self.travel_time = travel_time
        self.coach_types = coach_types
        self.source_station = source_station
        self.destination_station = destination_station
        self.departure_time = departure_time
        self.arrival_time = arrival_time

    def __repr__(self):
        return 'Train(%r, %r, %r, %r, %r, %r, %r, %r, %r)' % (
            self.category,
            self.model,
            self.num,
            self.travel_time,
            self.coach_types,
            self.source_station,
            self.destination_station,
            self.departure_time,
            self.arrival_time)

    def __str__(self):
        return '%s: %s - %s, %s' % (
            self.num,
            self.source_station,
            self.destination_station,
            self.departure_time)

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def info(self):
        parts = [(
            'Train: %(num)s\n'
            'Departure time: %(dept_date)s\n'
            'Travel time: %(travel_time)s\n'
            '~~~~~~~~~~'
        ) % {
            'num': self.num,
            'dept_date': self.departure_time,
            'arr_date': self.arrival_time,
            'travel_time': self.travel_time,
        }]
        parts += ['%s' % i for i in self.coach_types]
        return '\n'.join(parts)

    @classmethod
    def from_dict(cls, dikt):
        return cls(
            category=dikt['category'],
            model=dikt['model'],
            num=dikt['num'],
            travel_time=dikt['travel_time'],
            coach_types=[CoachType.from_dict(i) for i in dikt['types']],
            source_station=Station(dikt['from']['station_id'],
                                   dikt['from']['station']),
            destination_station=Station(dikt['till']['station_id'],
                                        dikt['till']['station']),
            departure_time=UZTimestamp.from_dict(dikt['from']),
            arrival_time=UZTimestamp.from_dict(dikt['till'])
        )

    @staticmethod
    def _station_point(uztimestamp, station):
        result = dict(
            station=station.title,
            station_id=station.id)
        result.update(uztimestamp.to_dict())
        return result

    def to_dict(self):
        result = dict(
            category=self.category,
            model=self.model,
            num=self.num,
            travel_time=self.travel_time,
            types=[i.to_dict() for i in self.coach_types],
            till=self._station_point(self.arrival_time,
                                     self.destination_station))
        result['from'] = self._station_point(
            self.departure_time, self.source_station)
        return result


class CoachType(object):

    def __init__(self, letter, places, title):
        self.letter = letter
        self.places = places
        self.title = title

    def __repr__(self):
        return 'CoachType(%r, %r, %r)' % (self.letter, self.places, self.title)

    def __str__(self):
        return '%s: %s (%s)' % (self.letter, self.places, self.title)

    @classmethod
    def from_dict(cls, dikt):
        return cls(*(dikt[i] for i in ('letter', 'places', 'title')))

    def to_dict(self):
        return dict(
            letter=self.letter,
            places=self.places,
            title=self.title)


class Coach(object):

    def __init__(self, allow_bonus, klass, type_id, has_bedding, num,
                 places_cnt, prices, reserve_price, services):
        self.allow_bonus = allow_bonus
        self.klass = klass
        self.type_id = type_id
        self.has_bedding = has_bedding
        self.num = num
        self.places_cnt = places_cnt
        self.prices = prices
        self.reserve_price = reserve_price
        self.services = services

    def __repr__(self):
        return 'Coach(%r %r %r %r %r %r %r %r %r)' % (
            self.allow_bonus,
            self.klass,
            self.type_id,
            self.has_bedding,
            self.num,
            self.places_cnt,
            self.prices,
            self.reserve_price,
            self.services)

    def __str__(self):
        return 'Coach %s' % self.num

    @classmethod
    def from_dict(cls, dikt):
        return cls(
            allow_bonus=dikt['allow_bonus'],
            klass=dikt['coach_class'],
            type_id=dikt['coach_type_id'],
            has_bedding=dikt['hasBedding'],
            num=dikt['num'],
            places_cnt=dikt['places_cnt'],
            prices=dikt['prices'],
            reserve_price=dikt['reserve_price'],
            services=dikt['services'])

    def to_dict(self):
        return dict(
            allow_bonus=self.allow_bonus,
            coach_class=self.klass,
            coach_type_id=self.type_id,
            hasBedding=self.has_bedding,
            num=self.num,
            places_cnt=self.places_cnt,
            prices=self.prices,
            reserve_price=self.reserve_price,
            services=self.services)


class Station(object):

    def __init__(self, id, title):
        self.id = id
        self.title = title

    def __repr__(self):
        return 'Station(%r, %r)' % (self.id, self.title)

    def __str__(self):
        return self.title

    def __eq__(self, other):
        return self.id == other.id

    @classmethod
    def from_dict(cls, dikt):
        return cls(dikt['station_id'], dikt['title'])

    def to_dict(self):
        return dict(
            station_id=self.id,
            title=self.title)


class UZTimestamp(object):
    """
    src_date != datetime.strftime()
    """

    def __init__(self, timestamp, str_date):
        self.timestamp = timestamp
        self.str_date = str_date
        self.datetime = datetime.fromtimestamp(timestamp)

    def __repr__(self):
        return 'UZTimestamp(%r, %r)' % (self.timestamp, self.str_date)

    def __str__(self):
        return self.str_date

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    @classmethod
    def from_dict(cls, dikt):
        return cls(dikt['date'], dikt['src_date'])

    def to_dict(self):
        return dict(
            date=self.timestamp,
            src_date=self.str_date
        )
