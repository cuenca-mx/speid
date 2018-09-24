FROM python:3.7
MAINTAINER Cuenca <dev@cuenca.com>

# Install app
ADD Makefile requirements.txt requirements-dev.txt /stpmex-handler/
WORKDIR /stpmex-handler
RUN make install
RUN pip install --quiet gunicorn

# Add repo contents to image
ADD . /stpmex-handler/

# Start celery
RUN pip install --quiet celery
COPY celeryd /etc/default/celeryd
CMD ["sh", "/etc/init.d/celeryd", "start"]


ENV PORT 3000
EXPOSE $PORT

CMD ["gunicorn", "--access-logfile=-", "--error-logfile=-", \
     "--bind=0.0.0.0:3000", "--workers=3", "speid:app"]
