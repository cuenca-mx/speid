FROM python:3.7

# Install app
ADD Makefile requirements.txt verify_certificate.pem /speid/
RUN mkdir /.aptible/
ADD .aptible/Procfile /.aptible/Procfile
WORKDIR /speid
RUN cp verify_certificate.pem
RUN update-ca-certificates
RUN pip install -qU pip
RUN pip install -q gunicorn
RUN make install

# Add repo contents to image
ADD . /speid/

ENV PORT 3000
EXPOSE $PORT
