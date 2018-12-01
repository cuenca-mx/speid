from werkzeug.serving import run_simple

from speid import app

from . import spei

from . import docker


@app.cli.command()
def serve():
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True,
               threaded=True)
