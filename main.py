#!

""" Fly Bulgarian. Display of flight information. """

import json
import re
import argparse
from datetime import datetime
from itertools import product
import requests
from lxml import html


def load_data(address):
    """
    Load html page from url.

    :param address: address of site or request

    :return: html page as an <html object>
    """

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                             " AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"
               }
    try:
        page_html = requests.get(address, headers=headers, timeout=(3, 10))
        tree = html.fromstring(page_html.content)
        result = tree
        page_html.raise_for_status()
        return result
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError("A Connection error"
                                                  "occurred.")
    except requests.exceptions.ReadTimeout:
        raise requests.exceptions.ReadTimeout("Read timeout occurred")
    except requests.exceptions.HTTPError as response:
        raise requests.exceptions.HTTPError("Code: {}".format(response))


def get_iata(page):
    """
    Get IATA-codes from page for
    checked on valid input.

    :param page: result of get_load(URL)

    :return: set with IATA-codes
    """

    try:
        form = page.xpath("./body/div[@id='wrapper']/div[@id='content']/"
                          "div[@id='reserve']/form[@id='reserve-form']")[0]

        options = form.xpath("./dl/dd[@class='double']/"
                             "select[@id='departure-city']/"
                             "option/@value")[1:]
        result = tuple(options)
        return result
    except (AttributeError, TypeError, IndexError):
        print("Incorrect result of load_data(address) function")


def input_data(page):
    """
    User input and validation check. Input continues
    until valid values are entered.
    Result of iata_code(page) and bug_list are used to validate user input.
    bug_list collects information about incorrect input and displays it after
    entered all the data.

    :param page: result of get_load(URL)

    :return: tuple with data -> (dep_iata, arr_iata, dep_date, arr_date)
    """

    while True:

        dep_iata = input("Enter flight details\n "
                         "in format departure city.arrival city."
                         "departure date[,departure city.arrival city."
                         "arrival date].number of seats: ")

        print(dep_iata.split(','))
        print(dep_iata.split('.'))
        is_data_valid(page)


def is_data_valid(page):
    """

    :param page:
    :return:
    """

    iata_codes = get_iata(page)
    # bug_list = []
    # code_message = "must be correct IATA-code: {}".format(iata_codes)
    # date_message = "must be correct date format: DD.MM.YYYY"

    # if (dep_iata not in iata_codes) or \
    #         (not dep_iata.isupper()):
    #     bug_list.append((dep_iata, code_message))
    #
    # if (arr_iata not in iata_codes) or \
    #         (not arr_iata.isupper()):
    #     bug_list.append((arr_iata, code_message))
    #
    # try:
    #     dep_date = datetime.strptime(dep_date, "%d.%m.%Y") \
    #         .date().strftime("%d.%m.%Y")
    #
    # except ValueError:
    #     bug_list.append((dep_date, date_message))
    #
    # if arr_date != "":
    #     try:
    #         arr_date = datetime.strptime(arr_date, "%d.%m.%Y") \
    #             .date().strftime("%d.%m.%Y")
    #     except ValueError:
    #         bug_list.append((arr_date, date_message))
    #
    # if bug_list:
    #     for bug in bug_list:
    #         print("Incorrect value: {} {}".format(bug[0], bug[1]))
    #     bug_list.clear()
    # else:
    #     return dep_iata, arr_iata, dep_date, arr_date


def get_search_request(values):
    """
    Get search page for parsing flight information.
    Tag <iframe> attribute <src> is used as request.

    :param values: result of input_data(page). If Arrival date(value[3])
                   is empty - use request for one-way flight.

    :return: load_data(request)
    """

    data = {"ow": "",
            "lang": "en",
            "depdate": values[2],
            "aptcode1": values[0],
            "aptcode2": values[1],
            "paxcount": 1,
            "infcount": ""}

    if len(values) > 3:
        data["rt"] = data.pop("ow")
        data.update(rtdate=values[3])

    request = requests.get("https://apps.penguin.bg/fly/quote3.aspx?",
                           params=data)

    tree = html.fromstring(request.content)
    result = tree

    return result


def get_flight_information(search_page):
    """
    Get flight information for entered data in input_data(page).
    Create going_out and coming_back lists with <tr> tags for
    Going Out and Coming Back flights.

    :param search_page: result of get_search_page(values)

    :return: For one-way - one_way_flight(going_out)
             For return - return_flight(combination)
             If no information - return "No available flights found."
    """

    result = "No available flights found."

    try:
        table = search_page.xpath("./body/form[@id='form1']/"
                                  "div[@style='padding: 10px;']/"
                                  "table[@id='flywiz']")[0]

        nested_table = table.xpath("//td/table[@id='flywiz_tblQuotes']")[0]

        tr_tag_list = nested_table.xpath(".//tr[@class='selectedrow']|"
                                         ".//tr[@class='notselrow']|"
                                         ".//tr[th[text()='Coming Back']]/"
                                         "th/text()")
    except IndexError:
        return result

    if tr_tag_list[:-1] == "Coming Back"\
            or not tr_tag_list\
            or len(tr_tag_list) == 1:
        return result

    # Division into going_out and coming_back lists
    if "Coming Back" in tr_tag_list:
        half = tr_tag_list.index("Coming Back")
        out = tr_tag_list[:half]
        back = tr_tag_list[half + 1:]
        going_out = (out[i:i+2] for i in range(len(out)) if i % 2 == 0)
        coming_back = (back[i:i+2] for i in range(len(back)) if i % 2 == 0)
        combination = product(going_out, coming_back)
        result = return_flight(combination)
    else:
        going_out = tuple(tr_tag_list)
        result = one_way_flight(going_out)

    return result


def one_way_flight(going_out):
    """
    Getting necessary information about one-way flight:
    - departure date;
    - arrival date;
    - price.

    :param going_out: list with <tr> tags.

    :return: tuple with flight information ((going out))
             and flight type -> ((departure date, arrival date,
             price), "one-way")
    """

    result = []

    for tr_tag in enumerate(going_out):
        if tr_tag[0] % 2 == 0:
            fly_date = tuple(tr_tag[1].xpath("./td/text()")[0:3])
            dep_time = datetime.strptime(fly_date[0] + fly_date[1],
                                         "%a, %d %b %y%H:%M")

            arr_time = datetime.strptime(fly_date[0] + fly_date[2],
                                         "%a, %d %b %y%H:%M")
        else:
            price = tr_tag[1].xpath("./td/text()")[0]
            reg = re.compile(r'(Price):\s{2}(\d{2,3}\.\d{2} EUR)')
            parse_price = reg.findall(price)
            result.append((dep_time, arr_time,
                           parse_price[0]))

    return tuple(result), "one-way"


def return_flight(combination):
    """
    Getting necessary information about return flight:
    - departure date for Going Out and Coming Back;
    - price.

    :param combination: list with <tr> tags.

    :return: tuple with flight information ((going out), (coming back))
    and flight type -> (((departure date, price),
     (departure date, price)), "return")
    """

    index = 0
    result = []

    for flights in combination:
        for flight in flights:
            fly_date = flight[0].xpath("./td/text()")[0:2]
            dep_time = datetime.strptime(fly_date[0] + fly_date[1],
                                         "%a, %d %b %y%H:%M")
            price = flight[1].xpath("./td/text()")[0]
            reg = re.compile(r'.(\d{2,3}\.\d{2})( EUR)')
            parse_price = reg.findall(price)

            if index % 2 == 0:
                out = (dep_time, parse_price[0])
                departure_date = dep_time
            else:
                arrival_date = dep_time
                if departure_date > arrival_date:
                    continue
                back = (dep_time, parse_price[0])
                result.append((out, back))
            index += 1
    return tuple(result), "return"


def data_generation(fly_data):
    """

    :param fly_data:

    :return: if get_flight_information(search_page) return
    "No available flights found." or no valid dates for
     return flight - return "No available flights found."
     else return flight information in json format:
     - one-way flight:
        [{
            "Date": "Sat, 06 Jul 19",
            "Departure time": "21:50",
            "Arrival time": "01:40",
            "Flight time": "3:50:00",
            "Class": "Standard",
            "Price": "160.00 EUR"
        }];
     - return flight:
        [{
            "Departure date": "Sat, 06 Jul 19 21:50",
            "Arrival date": "Sat, 13 Jul 19 16:00",
            "Class": "Standard",
            "Price": "253.0 EUR"
        }].
     Return flight results sorted by price.
    """

    if fly_data[1] == "one-way":
        price = fly_data[0][0][2][0]
        fly_dict_keys = ("Date", "Departure time", "Arrival time",
                         "Flight time", "Class", price)

        fly_dict_values = (
            (flight[0].strftime("%a, %d %b %y"),
             flight[0].strftime("%H:%M"),
             flight[1].strftime("%H:%M"),
             str(flight[1] - flight[0])[-7:],
             "Standard",
             flight[2][1]) for flight in fly_data[0])

    else:
        fly_dict_keys = ("Departure date", "Arrival date", "Class",
                         "Price")

        fly_dict_values = (
            (flight[0][0].strftime("%a, %d %b %y %H:%M"),
             flight[1][0].strftime("%a, %d %b %y %H:%M"),
             "Standard",
             str(float(flight[0][1][0]) +
                 float(flight[1][1][0])) +
             flight[0][1][1]) for flight in fly_data[0])

    flight_list = ({key: value for key, value in zip(fly_dict_keys, values)}
                   for values in fly_dict_values)

    result = sorted(flight_list, key=lambda price_key:
                    max(price_key.items()))
    result = json.dumps(result, indent=4)
    return result


def scrape(*args):
    """
    Main function. Call other functions and
    generates flight information in json format.
    If function is called with arguments *args, then they are
    passed to the get_search_page(values), else called input_data(page).

    :param args: Flight parameters: departure IATA-code,
                 Arrival IATA-code, Departure date, Arrival Date.
    For example: "CPH", "VAR", "02.07.2019", "13.07.2019",
                 "CPH", "VAR", "02.07.2019".
    Parameters transmitted only in that order.

    :return:
    """

    url = "http://www.flybulgarien.dk/en/"

    data = load_data(url)
    if not args:
        value = input_data(data)
    else:
        value = args
    search_page = get_search_request(value)
    flights = get_flight_information(search_page)
    if isinstance(flights, str):
        result = flights
    else:
        result = data_generation(flights)
    return result


if __name__ == '__main__':
    print(scrape("CPH", "VAR", "02.03.2019", "13.03.2019"))
    print(scrape("CPH", "VAR", "02.07.2019"))
    print(scrape("CPH", "VAR", "02.07.2019", "13.07.2019"))
    print(scrape("BLL", "BOJ", "17.07.2019"))
    # print(scrape())
