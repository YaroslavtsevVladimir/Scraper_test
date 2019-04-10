#!

""" Test for Fly Bulgarian scraper."""

from datetime import datetime
import pytest
import requests
from lxml import html
from main import send_request, get_flight_information,\
    NoResultException

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


# Test get_flight_information()
def test_get_flight_information_one_way():
    one_way_page = 'Static_pages/one_way_flight.html'

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree
    result = tuple([(datetime(2019, 7, 2, 21, 50),
                     datetime(2019, 7, 2, 1, 40),
                     ('Price', '207.00 EUR'))])

    assert get_flight_information(search, USER_DATA) == result


def test_get_flight_information_one_way_empty():
    one_way_page = 'Static_pages/one_way_flight_empty.html'

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree
    result = 'No available flights found.'
    assert get_flight_information(search, USER_DATA) == result


def test_get_flight_information_return():
    return_page = 'Static_pages/return_flight.html'

    with open(return_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree
    result = tuple([((datetime(2019, 7, 2, 21, 50), 'Copenhagen (CPH)',
                      'Varna (VAR)', ('207.00', ' EUR')),
                     (datetime(2019, 7, 8, 16, 0), 'Burgas (BOJ)',
                      'Billund (BLL)', ('119.00', ' EUR'))),
                    ((datetime(2019, 7, 2, 21, 50), 'Copenhagen (CPH)',
                      'Varna (VAR)', ('207.00', ' EUR')),
                     (datetime(2019, 7, 15, 16, 0), 'Burgas (BOJ)',
                      'Billund (BLL)', ('185.00', ' EUR')))])

    assert get_flight_information(search, USER_DATA) == result


def test_get_flight_information_return_empty():
    return_page = 'Static_pages/return_flight_empty.html'

    with open(return_page, 'r') as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree
    result = 'No available flights found.'
    assert get_flight_information(search, USER_DATA) == result


def test_get_flight_information_err():
    empty_req = 'https://apps.penguin.bg/fly/quote3.aspx?'
    data = {'ow': '', 'depdate': '', 'aptcode1': '', 'aptcode2': '',
            'paxcount': '', 'infcount': '', 'lang': 'en'}

    page = send_request(empty_req, data)
    search = page
    try:
        get_flight_information(search, USER_DATA)
    except (IndexError, NoResultException):
        pytest.fail('No available flights found.')


# Test get_data(*args)
# def test_scrape():
#     result = 'No available flights found.'
#     assert scrape() == result
