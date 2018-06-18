import datetime

import flask_sqlalchemy as fsa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import DetachedInstanceError


class Model(fsa.Model):

    def __repr__(self):
        cols = self.__mapper__.c.keys()
        class_name = self.__class__.__name__
        try:
            items = ', '.join([
                f'{col}={repr(getattr(self, col))}' for col in cols
            ])
        except DetachedInstanceError:
            items = '<detached>'
        return f'{class_name}({items})'

    def to_dict(self):
        rv = {}
        cols = self.__mapper__.c.keys()
        for col in cols:
            value = getattr(self, col)
            if type(value) is datetime.datetime:
                value = str(value)
            rv[col] = value
        return rv


db = fsa.SQLAlchemy(model_class=declarative_base(
    cls=Model, metaclass=fsa.model.DefaultMeta, name='Model'))
