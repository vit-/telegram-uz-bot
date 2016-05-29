#!/usr/bin/env bash

find . -iname '.coverage' -delete
find . -iname 'coverage.xml' -delete
find . -iname '*.pyc' -delete
find . -iname '__pycache__' -delete
find . -iname '.cache' -delete
