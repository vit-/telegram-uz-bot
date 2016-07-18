FROM python:3.5-alpine
MAINTAINER Vitalii Vokhmin <vitaliy.vokhmin@gmail.com>

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/app
RUN py.test -m 'not live'

ENV TG_BOT_TOKEN ''
ENV TG_BOT_NAME 'uz_ticket_bot'
ENV SCAN_DALAY_SEC 60
ENV STATSD_HOST ''
ENV STATSD_PORT 8125

CMD [ "python", "run_app.py" ]
