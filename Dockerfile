FROM python:3.5-onbuild
MAINTAINER Vitalii Vokhmin <vitaliy.vokhmin@gmail.com>

ENV TG_BOT_TOKEN ''
ENV STATSD_HOST 'dd-agent'
ENV STATSD_PORT 8125


RUN find . -iname '*.pyc' -delete && py.test -m 'not live'
CMD [ "python", "tg_bot.py" ]
