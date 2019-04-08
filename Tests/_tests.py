#!

""" Test for Fly Bulgarian scraper."""

from datetime import datetime
import pytest
import requests
from lxml import html
from main import send_request, get_iata, get_flight_information, scrape
from classes import NoResultException


# Test load_data()
def test_send_request():
    url = "http://www.google.com"
    page_html = requests.get(url)
    tree = html.fromstring(page_html.content)
    assert type(send_request(url)) == type(tree)


def test_send_request_http_err():
    http_url = "http://www.google.com/nothere"

    with pytest.raises(requests.exceptions.HTTPError) as response:
        send_request(http_url)
    print(response)


def test_send_request_connect_err():
    connect_url = "http://www.google"

    with pytest.raises(requests.exceptions.ConnectionError) as response:
        send_request(connect_url)
    print(response)


# Test get_iata()
def test_get_iata():
    codes = get_iata()
    assert codes == ('CPH', 'BLL', 'PDV', 'BOJ', 'SOF', 'VAR')


def test_get_iata_error():
    try:
        get_iata()
    except (AttributeError, TypeError, IndexError):
        pytest.fail("Incorrect result of load_data(address) function")


# Test get_flight_information()
def test_get_flight_information_one_way():
    one_way_page = "Static_pages/one_way_flight.html"

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree
    result = tuple([(datetime(2019, 7, 2, 21, 50),
                     datetime(2019, 7, 2, 1, 40),
                     ('Price', '207.00 EUR'))]), "one-way"

    assert get_flight_information(search) == result


def test_get_flight_information_one_way_empty():
    one_way_page = "Static_pages/one_way_flight_empty.html"

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree
    result = "No available flights found."
    assert get_flight_information(search) == result


def test_get_flight_information_return():
    return_page = "Static_pages/return_flight.html"

    with open(return_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
    search = tree
    result = tuple([((datetime(2019, 7, 2, 21, 50), "Copenhagen (CPH)",
                      "Varna (VAR)", ('207.00', ' EUR')),
                     (datetime(2019, 7, 8, 16, 0), "Burgas (BOJ)",
                      "Billund (BLL)", ('119.00', ' EUR'))),
                    ((datetime(2019, 7, 2, 21, 50), "Copenhagen (CPH)",
                      "Varna (VAR)", ('207.00', ' EUR')),
                     (datetime(2019, 7, 15, 16, 0), "Burgas (BOJ)",
                      "Billund (BLL)", ('185.00', ' EUR')))]),\
        "return"

    assert get_flight_information(search) == result


def test_get_flight_information_return_empty():
    return_page = "Static_pages/return_flight_empty.html"

    with open(return_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree
    result = "No available flights found."
    assert get_flight_information(search) == result


def test_get_flight_information_err():
    empty_req = "https://apps.penguin.bg/fly/quote3.aspx?ow=&lang=en&" \
                "depdate=&aptcode1=&aptcode2=&paxcount=1&infcount="

    page = send_request(empty_req)
    search = page
    try:
        get_flight_information(search)
    except (IndexError, NoResultException):
        pytest.fail("No available flights found.")


# Test get_data(*args)
def test_get_data():
    result = "No available flights found."
    assert scrape("CPH", "BOJ", "26.04.2019") == result
