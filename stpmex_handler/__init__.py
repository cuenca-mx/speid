import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database_uri = os.getenv('DATABASE_URI')
stpmex_handler_env = os.getenv('STPMEX_HANDLER_ENV', '')

app = Flask('stpmex-handler')

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


import stpmex_handler.models

if not stpmex_handler_env.lower() == 'prod':
    import stpmex_handler.commands
