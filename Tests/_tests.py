#!

""" Test for Fly Bulgarien scraper. """

import pytest
from lxml import html
from main import load_data, get_iata, get_flight_information,\
    get_search_page, one_way_flight, return_flight, get_data

#Test load_data
def test_load_data():
    pass


# Test get_iata()
def test_get_iata():
    main_page = "Fly Bulgarien.html"
    with open(main_page, "r") as page:
        reader = page.read()
        tree = html.fromstring(reader)
        codes = get_iata(tree)
    assert codes == ('CPH', 'BLL', 'PDV', 'BOJ', 'SOF', 'VAR')


def test_get_iata_err():
    url = "https://apps.penguin.bg/fly/quote3.aspx?rt=&lang=en&" \
          "depdate=26.06.2019&aptcode1=CPH&rtdate=10.07.2019&" \
          "aptcode2=BOJ&paxcount=1&infcount="

    page = load_data(url)
    try:
        get_iata(page)
    except (AttributeError, TypeError, IndexError):
        pytest.fail("Incorrect result of load_data(address) function")


