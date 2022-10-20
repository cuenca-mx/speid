from datetime import date, datetime

from speid.utils import get_next_business_day


def test_get_next_business_day_weekday():
    # monday
    today = datetime(2021, 2, 8)
    bd = get_next_business_day(today)
    # date should be the same because it is
    # a working day
    assert bd == date(today.year, today.month, today.day)


def test_get_next_business_day_weekend():
    # saturday
    today = date(2021, 2, 13)
    bd = get_next_business_day(today)
    # date should be moved to monday because
    # it is a weekend
    assert bd == date(2021, 2, 15)


def test_get_next_business_day_holiday():
    # holiday
    today = date(2021, 2, 1)
    bd = get_next_business_day(today)
    # date should be moved to tuesday because
    # it is a holiday
    assert bd == date(2021, 2, 2)


def test_get_next_business_day_holiday_friday():
    # holiday on friday
    today = date(2021, 1, 1)
    bd = get_next_business_day(today)
    # date should be moved to next monday because
    # it is a holiday
    assert bd == date(2021, 1, 4)


def test_get_next_business_day_bank_holiday():
    today = datetime(2021, 11, 2)
    bd = get_next_business_day(today)
    assert bd == date(2021, 11, 3)

    today = datetime(2021, 12, 12)
    bd = get_next_business_day(today)
    assert bd == date(2021, 12, 13)

    today = datetime(2023, 4, 6)
    bd = get_next_business_day(today)
    assert bd == date(2023, 4, 10)  # holy week and weekend
