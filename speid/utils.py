import os
from functools import wraps

from flask import jsonify, make_response

from . import app

WEEKEND = [5, 6]
BEGIN_HOLY_WEEK = os.getenv('BEGIN_HOLY_WEEK', '2023-04-06')
END_HOLY_WEEK = os.getenv('END_HOLY_WEEK', '2023-04-07')
HOLY_WEEK_DATES = eval(
    os.getenv(
        'HOLY_WEEK_DATES',
        '[("2023-04-06","2023-04-07"), ("2024-03-28","2024-03-29")]',
    )
)


def post(rule: str, **options):
    def decorator(view):
        @wraps(view)
        def decorated(*args, **kwargs):
            status_code, body = view(*args, **kwargs)
            return make_response(jsonify(body), status_code)

        endpoint = options.pop('endpoint', None)
        app.add_url_rule(
            rule, endpoint, decorated, methods=['POST'], **options
        )
        return view

    return decorator
