FROM python:3.5-onbuild
MAINTAINER Vitalii Vokhmin <vitaliy.vokhmin@gmail.com>

ENV TG_BOT_TOKEN ''

RUN find . -iname '*.pyc' -delete && py.test -m 'not live'
CMD [ "python", "tg_bot.py" ]
