from stpmex_handler import app


@app.route('/')
def health_check():
    return "I'm healthy!"


@app.route('/stp')
def callback_handler():
    pass
