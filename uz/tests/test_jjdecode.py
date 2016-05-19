import os
import pytest
from uz.jjdecode import JJDecoder


def read_file(path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, path)) as f:
        return f.read()


@pytest.fixture
def encoded():
    return read_file('fixtures/jj_encoded.txt')


@pytest.fixture
def encoded2():
    return read_file('fixtures/jj_encoded2.txt')


def test_jjdecoder(encoded, encoded2):
    assert JJDecoder(encoded).decode() == "alert('hello');"
    assert JJDecoder(encoded2).decode() == "alert('this is a test JJ encoded sample');"  # noqa
