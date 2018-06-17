from werkzeug.serving import run_simple

from stpmex_handler import app


@app.cli.command()
def serve():
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True,
               threaded=True)
