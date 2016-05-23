FROM python:3.5-onbuild
MAINTAINER Vitalii Vokhmin <vitaliy.vokhmin@gmail.com>

ENV TG_BOT_TOKEN ''
ENV DATADOG_API_KEY ''
ENV DATADOG_APP_KEY ''
ENV STATSD_HOST 'dockerhost'
ENV STATSD_PORT 8125


RUN find . -iname '*.pyc' -delete && py.test -m 'not live'
CMD [ "python", "tg_bot.py" ]
