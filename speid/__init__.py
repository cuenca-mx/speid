import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database_uri = os.getenv('DATABASE_URI')
speid_env = os.getenv('SPEID_ENV', '')

app = Flask('speid')

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


import speid.models
import speid.views

if not speid_env.lower() == 'prod':
    import speid.commands
