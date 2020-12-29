from datetime import datetime

from speid.helpers.task_helpers import time_in_range


def test_time_in_range():

    st = datetime(2020, 12, 28, 23, 55)
    et = datetime(2020, 12, 28, 0, 5)
    dn = datetime(2020, 12, 28, 0, 3)
    assert time_in_range(st, et, dn)

    dn = datetime(2020, 12, 28, 1, 3)
    assert not time_in_range(st, et, dn)

    st = datetime(2020, 12, 28, 0, 55)
    et = datetime(2020, 12, 28, 1, 5)
    dn = datetime(2020, 12, 28, 0, 57)
    assert time_in_range(st, et, dn)
