FROM python:2.7.15-slim-stretch
MAINTAINER developer@knowledge-fusion.science


ENV CELERY_BEAT_SCHEDULE=/var/run/celery_beat_schedule

RUN mkdir /usr/src/app
WORKDIR /usr/src/app
ENV PYTHONPATH $PYTHONPATH:/usr/src/app

# Backend dependencies
COPY requirements*txt /usr/src/app/
RUN set -ex \
	&& buildDeps=' \
		curl \
		gcc \
		libbz2-dev \
    libc6-dev \
    libffi-dev \
		libssl-dev \
    g++ \
	' \
	&& apt-get update && apt-get install -y $buildDeps --no-install-recommends \
  && apt-get install -y git --no-install-recommends \
  && pip install --no-cache-dir -r requirements_prod.txt \
  && rm -rf /root/.cache/ \
  && rm -rf /var/lib/apt/lists/* \
  && rm requirements.txt \
  && apt-get purge -y --auto-remove $buildDeps


# build from source
COPY . /usr/src/app

EXPOSE 5100

ENTRYPOINT ["/usr/src/app/entry.sh"]
CMD ["?"]