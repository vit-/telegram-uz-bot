FROM python:3.5-onbuild
MAINTAINER Vitalii Vokhmin <vitaliy.vokhmin@gmail.com>

ENV TG_BOT_TOKEN ''
ENV TG_BOT_NAME 'uz_ticket_bot'
ENV SCAN_DALAY_SEC 60
ENV STATSD_HOST 'dd-agent'
ENV STATSD_PORT 8125


RUN py.test -m 'not live'
CMD [ "python", "run_app.py" ]
