from stpmex_handler.tables import requests

from .base import db


class Request(db.Model):
    __table__ = requests
