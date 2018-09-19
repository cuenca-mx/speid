import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask('stpmex-handler')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Al final debería de eliminarse las siguientes líneas para guardar en RabbitMQ
db = SQLAlchemy(app)
migrate = Migrate(app, db)

if not os.getenv('STPMEX_HANDLER_ENV', '').lower() == 'prod':
    import stpmex_handler.commands
