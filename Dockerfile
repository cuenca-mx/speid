FROM python:3.7
MAINTAINER Cuenca <dev@cuenca.com>

# Install app
ADD Makefile requirements.txt /speid/
WORKDIR /speid
RUN pip install -qU pip
RUN pip install -q gunicorn
RUN make install

# Add repo contents to image
ADD . /speid/

ENV PORT 3000
EXPOSE $PORT

CMD NEW_RELIC_LICENSE_KEY=${NEW_RELIC_LICENSE_KEY} NEW_RELIC_APP_NAME=speid newrelic-admin run-program celery worker -A speid.tasks.celery -D --loglevel=info -c 5 -Q cuenca.stp.account,cuenca.stp.new_order,recon.stp.transaction && \
    NEW_RELIC_LICENSE_KEY=${NEW_RELIC_LICENSE_KEY} NEW_RELIC_APP_NAME=speid newrelic-admin run-program gunicorn --access-logfile=- --error-logfile=- --bind=0.0.0.0:3000 --workers=${SPEID_WORKERS:-5} speid:app
