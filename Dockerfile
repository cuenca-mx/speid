FROM python:3.7
MAINTAINER Cuenca <dev@cuenca.com>

# Install app
ADD Makefile requirements.txt /speid/
WORKDIR /speid
RUN pip install -q --upgrade pip
RUN pip install --quiet gunicorn
RUN make install

# Add repo contents to image
ADD . /speid/

ENV PORT 3000
EXPOSE $PORT

CMD gunicorn --access-logfile=- --error-logfile=- --bind=0.0.0.0:3000 --workers=5 speid:app