import pytest

from uz.client.jjdecode import JJDecoder
from uz.tests import read_file


@pytest.fixture
def encoded():
    return read_file('fixtures/jj_encoded.txt')


@pytest.fixture
def encoded2():
    return read_file('fixtures/jj_encoded2.txt')


def test_jjdecoder(encoded, encoded2):
    assert JJDecoder(encoded).decode() == "alert('hello');"
    assert JJDecoder(encoded2).decode() == "alert('this is a test JJ encoded sample');"  # noqa
