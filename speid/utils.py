import datetime as dt
import os
from functools import wraps

from flask import jsonify, make_response
from workalendar.america import Mexico

from . import app

WEEKEND = [5, 6]
BEGIN_HOLY_WEEK = os.getenv('BEGIN_HOLY_WEEK', '2023-04-06')
END_HOLY_WEEK = os.getenv('END_HOLY_WEEK', '2023-04-07')


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


def get_next_business_day(fecha: dt.date) -> dt.date:
    """
    Obtains the next business day in case the current one is not.
    """
    mx = Mexico()
    holidays = [hol[0] for hol in mx.holidays(fecha.year)]

    begin = dt.date.fromisoformat(BEGIN_HOLY_WEEK)
    end = dt.date.fromisoformat(END_HOLY_WEEK)
    holy_week = [
        begin + dt.timedelta(days=n)
        for n in range(int((end - begin).days) + 1)
    ]
    bank_holiday = holy_week + [
        dt.date(fecha.year, 11, 2),
        dt.date(fecha.year, 12, 12),
    ]
    holidays += bank_holiday

    business_day = dt.date(fecha.year, fecha.month, fecha.day)
    while business_day.weekday() in WEEKEND or business_day in holidays:
        business_day = business_day + dt.timedelta(days=1)

    return business_day
