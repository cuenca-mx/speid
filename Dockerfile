FROM python:3.7
MAINTAINER Cuenca <dev@cuenca.com>

# Install app
ADD Makefile requirements.txt requirements-dev.txt /speid/
WORKDIR /speid
RUN make install
RUN pip install --quiet gunicorn

# Add repo contents to image
ADD . /speid/

# Start celery
COPY speid/daemon/celeryd-daemon /etc/init.d/celeryd
COPY speid/daemon/celeryd-conf /etc/default/celeryd
RUN mkdir -p /etc/default
RUN chmod +x /etc/init.d/celeryd
RUN adduser celery --disabled-password
RUN mkdir -p /var/log/celery/ && chown celery:celery /var/log/celery/
RUN mkdir -p /var/run/celery/ && chown celery:celery /var/run/celery/
RUN pip install --quiet celery
#CMD ["sh", "-c", "/etc/init.d/celeryd start"]

ENV PORT 3000
EXPOSE $PORT

#CMD ["gunicorn", "--access-logfile=-", "--error-logfile=-", \
#     "--bind=0.0.0.0:3000", "--workers=3", "speid:app"]

CMD /etc/init.d/celeryd start && gunicorn --access-logfile=- --error-logfile=- --bind=0.0.0.0:3000 --workers=3 speid:app
