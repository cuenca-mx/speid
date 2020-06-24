from functools import wraps

from flask import jsonify, make_response

from . import app


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
