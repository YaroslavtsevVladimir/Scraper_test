#!

""" Test for Fly Bulgarian scraper."""

import pytest
import requests
from main import send_request, is_data_valid, InvalidData

URL = 'http://www.google.com/nothere'
USER_DATA = {"dep_city": "CPH", "arr_city": "VAR",
             "dep_date": '15.07.2019',
             "arr_date": "20.07.2019",
             "num_seats": "2"}


# Test load_data()
def test_send_request_http_err():
    data = ''
    try:
        send_request(data)
    except pytest.raises(requests.exceptions.HTTPError):
        pytest.fail('HTTPError')


def test_send_request_connect_err():
    data = ''
    try:
        send_request(data)
    except pytest.raises(requests.exceptions.ConnectionError):
        pytest.fail('ConnectionError')


# Test is_data_valid()
def test_is_data_valid_few_args():
    user_data = {'dep_city': 'CPH',
                 'arr_city': 'VAR',
                 'dep_date': None,
                 'arr_date': None,
                 'num_seats': None
                 }

    with pytest.raises(InvalidData):
        is_data_valid(user_data)


def test_is_data_valid_many_args():
    user_data = {'dep_city': 'CPH',
                 'arr_city': 'VAR',
                 'dep_date': '15.07.1229',
                 'arr_date': '16.07.2019',
                 'num_seats': None,
                 'something': 24,
                 'date': '15.12.2020'
                 }

    with pytest.raises(InvalidData):
        is_data_valid(user_data)


def test_is_data_valid_city_err():
    user_data = {'dep_city': 'cph',
                 'arr_city': 'VAR',
                 'dep_date': '15.07.2019',
                 'arr_date': '20.07.2019',
                 'num_seats': 2}

    with pytest.raises(InvalidData):
        is_data_valid(user_data)


def test_is_data_valid_date_err():
    user_data = {'dep_city': 'CPH',
                 'arr_city': 'VAR',
                 'dep_date': '15.15.2019',
                 'arr_date': '20.07.2019',
                 'num_seats': 2}

    with pytest.raises(InvalidData):
        is_data_valid(user_data)


def test_is_data_valid_num_seats_err():
    user_data = {'dep_city': 'cph',
                 'arr_city': 'VAR',
                 'dep_date': '15.07.2019',
                 'arr_date': '20.07.2019',
                 'num_seats': 25}

    with pytest.raises(InvalidData):
        is_data_valid(user_data)
