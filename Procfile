web: exec gunicorn --access-logfile=- --error-logfile=- --bind=0.0.0.0:$PORT --workers=3 speid:app
worker: chmod -R a+rxw /etc/hosts && exec /etc/init.d/celeryd start