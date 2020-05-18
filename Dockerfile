FROM python:3.7-alpine

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE config.settings
ENV TZ=Europe/Moscow

WORKDIR /usr/src/app

RUN set -ex \
    && addgroup -g 82 -S www-data \
    && adduser -u 82 -D -S -G www-data www-data \
    && apk add --upgrade --no-cache --virtual .build-deps \
        openssl-dev \
    && apk add --upgrade --virtual \
        build-base \
        gcc \
        python3-dev \
        musl-dev \
    && pip3 install cython=='0.29.15' \
    && apk add --upgrade \
        postgresql-dev \
        libffi-dev \
        freetds-dev \
        tzdata \
        py-cffi \
        tzdata \
    && apk --no-cache add --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing watchman

COPY . /usr/src/app

COPY docker/services/self-service/app/gunicorn.conf /gunicorn.conf

RUN set -ex \
    && pip install -r /usr/src/app/requirements.txt --no-cache-dir \
    && apk del --no-cache .build-deps \
    && chown -R www-data:www-data /usr/src/app

EXPOSE 8000

CMD ["gunicorn", "--config", "/gunicorn.conf", "config.wsgi:application"]
