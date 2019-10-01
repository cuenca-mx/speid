from functools import wraps

from flask import jsonify, make_response

from speid import app


def get(rule, **options):
    def decorator(view):
        @wraps(view)
        def decorated(*args, **kwargs):
            status_code, body = view(*args, **kwargs)
            return make_response(jsonify(body), status_code)

        endpoint = options.pop('endpoint', None)
        app.add_url_rule(rule, endpoint, decorated, methods=['GET'], **options)
        return view

    return decorator


def patch(rule, **options):
    def decorator(view):
        @wraps(view)
        def decorated(*args, **kwargs):
            status_code, body = view(*args, **kwargs)
            return make_response(jsonify(body), status_code)

        endpoint = options.pop('endpoint', None)
        app.add_url_rule(
            rule, endpoint, decorated, methods=['PATCH'], **options
        )
        return view

    return decorator


def post(rule, **options):
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
