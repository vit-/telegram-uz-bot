import os


def read_file(path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, path)) as f:
        return f.read()
