import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask('stpmex-handler')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


import stpmex_handler.views
import stpmex_handler.models

if not os.getenv('STPMEX_HANDLER_ENV', '').lower() == 'prod':
    import stpmex_handler.commands
