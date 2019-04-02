#!

""" Test for Fly Bulgarien scraper. """

from datetime import datetime
import pytest
import requests
import json
from lxml import html
from main import load_data, get_iata, get_flight_information, get_data


# Test load_data()
def test_load_data():
    url = "http://www.google.com"
    page_html = requests.get(url)
    tree = html.fromstring(page_html.content)
    assert type(load_data(url)) == type(tree)


def test_load_data_http_err():
    http_url = "http://www.google.com/nothere"

    with pytest.raises(requests.exceptions.HTTPError) as response:
        load_data(http_url)
    print(response)


def test_load_data_connect_err():
    connect_url = "http://www.google"
    with pytest.raises(requests.exceptions.ConnectionError) as response:
        load_data(connect_url)
    print(response)


# Test get_iata()
def test_get_iata():
    main_page = "Fly Bulgarien.html"
    with open(main_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
        codes = get_iata(tree)
    assert codes == ('CPH', 'BLL', 'PDV', 'BOJ', 'SOF', 'VAR')


def test_get_iata_err():
    req = "https://apps.penguin.bg/fly/quote3.aspx?rt=&lang=en&" \
          "depdate=26.06.2019&aptcode1=CPH&rtdate=10.07.2019&" \
          "aptcode2=BOJ&paxcount=1&infcount="

    page = load_data(req)
    try:
        get_iata(page)
    except (AttributeError, TypeError, IndexError):
        pytest.fail("Incorrect result of load_data(address) function")


# Test get_flight_information()
def test_get_flight_information_one_way():
    one_way_page = "one_way_flight.html"

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree, "one-way"
    result = tuple([(datetime(2019, 7, 2, 21, 50),
                     datetime(2019, 7, 2, 1, 40),
                     ('Price:', '207.00 EUR'))]), "one-way"

    assert get_flight_information(search) == result


def test_get_flight_information_one_way_empty():
    one_way_page = "one_way_flight_empty.html"

    with open(one_way_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree, "one-way"
    result = tuple([]), "one-way"
    assert get_flight_information(search) == result


def test_get_flight_information_return():
    return_page = "return_flight.html"

    with open(return_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree, "return"
    result = tuple([((datetime(2019, 7, 2, 21, 50), ('207.00', ' EUR')),
                     (datetime(2019, 7, 8, 16, 0), ('119.00', ' EUR'))),
                    ((datetime(2019, 7, 2, 21, 50), ('207.00', ' EUR')),
                     (datetime(2019, 7, 15, 16, 0), ('185.00', ' EUR')))]),\
        "return"

    assert get_flight_information(search) == result


def test_get_flight_information_return_empty():
    return_page = "return_flight_empty.html"

    with open(return_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)

    search = tree, "return"
    result = "No available flights found."
    assert get_flight_information(search) == result


def test_get_flight_information_index_err():
    empty_req = "https://apps.penguin.bg/fly/quote3.aspx?ow=&lang=en&" \
                "depdate=&aptcode1=&aptcode2=&paxcount=1&infcount="

    page = load_data(empty_req)
    search = page, 'one-way'
    try:
        get_flight_information(search)
    except IndexError:
        pytest.fail("No available flights found.")


# Test get_data(*args)
def test_get_data():
    result = "No available flights found."
    assert get_data("CPH", "BOJ", "26.04.2019") == result
