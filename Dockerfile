FROM python:3.6
MAINTAINER Matin Tamizi <matin@cuenca.io>

RUN pip install --quiet gunicorn

# Install app
ADD Makefile requirements.txt /stpmex-handler/
WORKDIR /stpmex-handler
RUN make install

# Add repo contents to image
ADD . /stpmex-handler/

ENV PORT 3000
EXPOSE $PORT

CMD ["gunicorn", "--access-logfile=-", "--error-logfile=-", \
     "--bind=0.0.0.0:3000", "--workers=3", "stpmex_handler:app"]
