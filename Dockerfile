FROM node:20-slim AS node

COPY ./package.json package.json
RUN npm install

FROM python:3.12 AS app
LABEL maintainer "DataMade <info@datamade.us>"

RUN apt-get update && \
	apt-get install -y --no-install-recommends --purge postgresql-client gdal-bin && \
	apt-get autoclean && \
	rm -rf /var/lib/apt/lists/* && \
	rm -rf /tmp/*

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# django-councilmatic's 5.x branch is missing a migration for its own
# models (see patches/councilmatic_core/migrations for details). Patch it
# into the installed package so `manage.py migrate` doesn't break.
COPY ./patches/councilmatic_core/migrations/0054_remove_person_councilmatic_biography_and_more.py \
	/usr/local/lib/python3.12/site-packages/councilmatic_core/migrations/0054_remove_person_councilmatic_biography_and_more.py

# Get NodeJS & npm
COPY --from=node /usr/local/bin /usr/local/bin
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules

# Get app dependencies
COPY --from=node node_modules /app/node_modules

COPY . /app
ENV DJANGO_SECRET_KEY 'foobar'
RUN python manage.py collectstatic --no-input

ENTRYPOINT ["/app/docker-entrypoint.sh"]
