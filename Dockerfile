FROM python:3.6
MAINTAINER Cuenca <dev@cuenca.com>

# Install app
ADD Makefile requirements.txt /speid/
WORKDIR /speid
RUN pip install --quiet --upgrade pip
RUN make install
RUN pip install --quiet gunicorn

# Add repo contents to image
ADD . /speid/

# Start celery
COPY speid/daemon/config/celeryd-daemon /etc/init.d/celeryd
COPY speid/daemon/config/celeryd-conf /etc/default/celeryd
RUN mkdir -p /etc/default
RUN chmod +x /etc/init.d/celeryd
RUN chmod -R a+rw /speid
RUN adduser celery --disabled-password
RUN mkdir -p /var/log/celery/ && chown celery:celery /var/log/celery/
RUN mkdir -p /var/run/celery/ && chown celery:celery /var/run/celery/
RUN pip install --quiet celery

ENV PORT 3000
EXPOSE $PORT

CMD honcho start