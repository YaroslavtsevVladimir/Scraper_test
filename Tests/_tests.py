#!

""" Test for Fly Bulgarian scraper."""

from datetime import datetime
import pytest
import requests
from lxml import html
from main import send_request, get_flight_information,\
    is_data_valid, InvalidData

USER_DATA = {"dep_city": "CPH", "arr_city": "VAR",
             "dep_date": '15.07.2019',
             "arr_date": "20.07.2019",
             "num_seats": "2"}


# Test load_data()
def test_send_request():

    url = 'http://www.flybulgarien.dk/script/getdates/2-departure'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/64.0.3282.140 Safari/537.36 '
                      'Edge/18.17763',
        'Host': 'www.flybulgarien.dk',
        'Content-Type': 'application/x-www-form-urlencoded'}

    data = 'code1=CPH&code2=BOJ'
    result = '[[2019,6,26],[2019,7,3]]'
    assert type(send_request('POST', url, headers, data)) == type(result)


def test_send_request_http_err():
    http_url = 'http://www.google.com/nothere'
    data = 'code1=CPH&code2=BOJ'
    with pytest.raises(requests.exceptions.HTTPError) as response:
        send_request(http_url, data)
    print(response)


def test_send_request_connect_err():
    connect_url = 'http://www.flybulgarien.en'
    data = {'': ''}
    with pytest.raises(requests.exceptions.ConnectionError) as response:
        send_request(connect_url, data)
    print(response)


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


def test_is_data_valid_iata_err():
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


# Test get_flight_information()
def test_get_flight_information_one_way():
    one_way_page = 'Static_pages/one_way_flight.html'
    user_data = {"dep_city": "CPH",
                 "arr_city": "VAR",
                 "dep_date": '02.07.2019',
                 "arr_date": None,
                 "num_seats": 2}

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree

    result = (({'dep_city': 'CPH', 'arr_city': 'VAR',
                'dep_date': datetime(2019, 7, 2, 21, 50),
                'arr_date': datetime(2019, 7, 2, 1, 40),
                'price': (207.0, ' EUR')},),)
    assert tuple(get_flight_information(search, user_data)) == result


def test_get_flight_information_one_way_empty():
    one_way_page = 'Static_pages/one_way_flight_empty.html'

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree

    result = 'No outbound flights'
    assert get_flight_information(search, USER_DATA) == result


def test_get_flight_information_return():
    return_page = 'Static_pages/return_flight.html'
    user_data = {"dep_city": "CPH",
                 "arr_city": "BOJ",
                 "dep_date": '26.06.2019',
                 "arr_date": "10.07.2019",
                 "num_seats": 1}

    with open(return_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree
    result = (({'dep_city': 'CPH',
                'arr_city': 'VAR',
                'dep_date': datetime(2019, 7, 2, 21, 50),
                'arr_date': datetime(2019, 7, 2, 1, 40),
                'price': (207.0, ' EUR')},
               {'dep_city': 'BOJ',
                'arr_city': 'BLL',
                'dep_date': datetime(2019, 7, 8, 16, 0),
                'arr_date': datetime(2019, 7, 8, 17, 50),
                'price': (119.0, ' EUR')}),
              ({'dep_city': 'CPH',
                'arr_city': 'VAR',
                'dep_date': datetime(2019, 7, 2, 21, 50),
                'arr_date': datetime(2019, 7, 2, 1, 40),
                'price': (207.0, ' EUR')},
               {'dep_city': 'BOJ',
                'arr_city': 'BLL',
                'dep_date': datetime(2019, 7, 15, 16, 0),
                'arr_date': datetime(2019, 7, 15, 17, 50),
                'price': (185.0, ' EUR')}))

    assert tuple(get_flight_information(search, user_data)) == result


def test_get_flight_information_return_out_empty():
    return_page = 'Static_pages/return_flight_out_empty.html'

    with open(return_page, 'r') as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree
    result = 'No outbound flights'
    assert get_flight_information(search, USER_DATA) == result


def test_get_flight_information_return_back_empty():
    return_page = 'Static_pages/return_flight_back_empty.html'

    with open(return_page, 'r') as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree
    result = 'No inbound flights'
    assert get_flight_information(search, USER_DATA) == result
