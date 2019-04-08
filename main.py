#!

""" Fly Bulgarian. Display of flight information. """

import json
import re
import argparse
from datetime import datetime, timedelta
from itertools import product
import requests
from lxml import html
from classes import InvalidData, NoResultException


def send_request(*args):
    """
    Load html page from url.

    :param args: request type or url,
                 headers and data

    :return: html page as an <html object>
    """

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                             "AppleWebKit/537.36 (KHTML, like Gecko)"
                             "Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"
               }

    try:
        if args[0] != "POST":
            request = requests.get(args[0], headers=headers, timeout=(3, 10))
            tree = html.fromstring(request.content)
            result = tree
        else:
            request = requests.post(args[1], headers=args[2], data=args[3],
                                    timeout=(3, 10))
            result = request.content.decode("utf-8")
        request.raise_for_status()
        return result
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError("A Connection error"
                                                  "occurred.")
    except requests.exceptions.ReadTimeout:
        raise requests.exceptions.ReadTimeout("Read timeout occurred")
    except requests.exceptions.HTTPError as response:
        raise requests.exceptions.HTTPError("Code: {}".format(response))


def get_iata():
    """
    Get IATA-codes from page for
    checked on valid input.

    :return: tuple with IATA-codes
    """

    url = "http://www.flybulgarien.dk/en/"
    page = send_request(url)

    try:
        form = page.xpath("./body/div[@id='wrapper']/div[@id='content']/"
                          "div[@id='reserve']/form[@id='reserve-form']")[0]

        options = form.xpath("./dl/dd[@class='double']/"
                             "select[@id='departure-city']/"
                             "option/@value")[1:]

        codes = tuple(options)
        return codes
    except (AttributeError, TypeError, IndexError):
        print("Incorrect result of load_data(address) function")


def get_available_date(iata_codes):
    """
    Use POST request to receive available date from main page for
    checked on valid input.

    :param iata_codes: result of get_iata()

    :return: tuple with start date and
    final date -> (datetime(2019, 7, 2), datetime(2019, 7, 25))
    """

    post_url = "http://www.flybulgarien.dk/script/getdates/2-departure"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/64.0.3282.140 Safari/537.36 "
                      "Edge/18.17763",
        "Host": "www.flybulgarien.dk",
        "Content-Type": "application/x-www-form-urlencoded"}

    data = "code1={}&code2={}".format(iata_codes[0], iata_codes[1])
    date_data = send_request("POST", post_url, headers, data)

    date_data = json.loads(date_data.split("-")[0])
    start_date = " ".join(map(str, date_data[0]))
    final_date = " ".join(map(str, date_data[-1]))
    start_date = datetime.strptime(start_date, "%Y %m %d").date()
    final_date = datetime.strptime(final_date, "%Y %m %d").date()
    return start_date, final_date


def input_data():
    """
    User input and validation check. Input continues
    until valid values are entered.

    :return: tuple with data -> (departure IATA-code,
             arrival IATA-code, departure date[, arrival date],
             number of seats)
    """

    while True:

        dep_iata = input("Enter flight details in format\n"
                         "departure city.arrival city."
                         "departure date[.arrival date]."
                         "number of seats: ")

        data_list = tuple(dep_iata.split('.'))
        values = is_data_valid(data_list)
        if values:
            return values


def is_data_valid(values):
    """
    Checked result of input_data() for correctness.
    Result of iata_code(page) and get_available_date(iata_codes)
    are used to validate user input.
    if data is incorrect, then exception InvalidData is called
    and print the message with information about incorrect value.

    :return: if exception InvalidData is called - message about
             incorrect value,
             else tuple -> (departure IATA-code, arrival IATA-code,
             departure date[, arrival date], number of seats))
    """

    iata_codes = get_iata()

    # Valid IATA-code check
    try:
        if (values[0] not in iata_codes) or \
                (values[1] not in iata_codes) or\
                (not values[0].isupper()) or\
                (not values[1].isupper()):
            raise InvalidData()

    except InvalidData:
        return print("Incorrect IATA-code. Must be in: {}".format(iata_codes))

    # Valid number of seats check
    try:
        num_seats = int(values[-1])
        if not 0 < num_seats <= 8:
            raise InvalidData()
    except (InvalidData, ValueError):
        return print("Incorrect numbers of seats. Must be in [1,8]")

    # Valid date check
    try:
        valid_codes = (values[0], values[1])
        date_list = get_available_date(valid_codes)
        leeway = timedelta(days=8)
        out_dates = (date_list[0] - leeway, date_list[-1] + leeway)

        dep_date = datetime.strptime(values[2], "%d/%m/%Y").date()

        if out_dates[0] < dep_date < out_dates[1]:
            dep_date = dep_date.strftime("%d.%m.%Y")
        else:
            raise InvalidData
        result = (values[0], values[1], dep_date, num_seats)

        if len(values) == 5:
            arr_date = datetime.strptime(values[3], "%d/%m/%Y").date()

            if out_dates[0] < arr_date < out_dates[1]:
                arr_date = arr_date.strftime("%d.%m.%Y")
            else:
                raise InvalidData

            result = (values[0], values[1], dep_date, arr_date, num_seats)
    except (InvalidData, ValueError, IndexError):
        return print("Incorrect date format. Must be DD/MM/YYYY,"
                     "and date should not be greater than {} "
                     "and {}.".format(out_dates[0], out_dates[1]))
    return result


def get_search_request(values):
    """
    Get search page for parsing flight information.
    Tag <iframe> attribute <src> is used as request.

    :param values: result of input_data(page). If Arrival date(value[3])
                   is empty - use request for one-way flight.

    :return: html page as an <html object>
    """

    data = {"ow": "",
            "lang": "en",
            "depdate": values[2],
            "aptcode1": values[0],
            "aptcode2": values[1],
            "paxcount": values[-1],
            "infcount": ""}

    if len(values) > 4:
        data["rt"] = data.pop("ow")
        data.update(rtdate=values[3])

    request = requests.get("https://apps.penguin.bg/fly/quote3.aspx?",
                           params=data, timeout=(3, 10))

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

        if tr_tag_list[:-1] == "Coming Back"\
                or not tr_tag_list\
                or len(tr_tag_list) == 1:

            raise NoResultException

    except (IndexError, NoResultException):
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
    - Information about going out and coming back flights;
    - departure date for going out and coming back;
    - price.

    :param combination: list with <tr> tags.

    :return: tuple with flight information ((going out), (coming back))
    and flight type -> (((departure city, arrival city, departure date, price),
     (departure city, arrival city, arrival date, price)), "return")
    """

    index = 0
    result = []

    for flights in combination:
        for flight in flights:
            fly_date = flight[0].xpath("./td/text()")[0:6]
            dep_time = datetime.strptime(fly_date[0] + fly_date[1],
                                         "%a, %d %b %y%H:%M")
            price = flight[1].xpath("./td/text()")[0]
            parse_price = re.findall(r'.(\d{2,3}\.\d{2})( EUR)', price)
            dep_city = fly_date[3]
            arr_city = fly_date[4]
            if index % 2 == 0:
                out = (dep_time, dep_city, arr_city, parse_price[0])
                departure_date = dep_time
            else:
                arrival_date = dep_time
                if departure_date > arrival_date:
                    continue
                back = (dep_time, dep_city, arr_city, parse_price[0])
                result.append((out, back))
            index += 1
    return tuple(result), "return"


def data_generation(fly_data):
    """
    Data processing and formation in json format.

    :param fly_data: result of one_way_flight(going_out) or
           return_flight(combination)

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
            "Going out": "Copenhagen (CPH) - Varna (VAR)",
            "Departure date": "Tue, 02 Jul 19 21:50",
            "Coming back": "Burgas (BOJ) - Billund (BLL)",
            "Arrival date": "Mon, 22 Jul 19 16:00",
            "Class": "Standard",
            "Price": "379.0 EUR"
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
        fly_dict_keys = ("Going out", "Departure date",
                         "Coming back", "Arrival date",
                         "Class", "Price")

        fly_dict_values = (
            ("{} - {}".format(flight[0][1], flight[0][2]),
             flight[0][0].strftime("%a, %d %b %y %H:%M"),
             "{} - {}".format(flight[1][1], flight[1][2]),
             flight[1][0].strftime("%a, %d %b %y %H:%M"),
             "Standard",
             str(float(flight[0][3][0]) +
                 float(flight[1][3][0])) +
             flight[0][3][1]) for flight in fly_data[0])

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
    passed to the get_search_request(values), else called input_data().

    :param args: flight parameters: departure IATA-code,
                 Arrival IATA-code, Departure date, Arrival Date, number of seats.
    For example: "CPH", "VAR", "02.07.2019", "13.07.2019", "1"
                 "CPH", "VAR", "02.07.2019", "3".
    Parameters transmitted only in that order.

    :return: information about flights in json format or
             "No available flights found."
    """

    if not args:
        value = input_data()
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
    print(scrape("CPH", "VAR", "02.03.2019", "13.03.2019", "1"))
    print(scrape("CPH", "VAR", "02.07.2019", "1"))
    print(scrape("CPH", "BOJ", "26.06.2019", "20.07.2019", "3"))
    print(scrape("BLL", "BOJ", "17.07.2019", "4"))
    print(scrape("CPH", "VAR", "02.07.2019", "02.08.2019", "2"))
    print(scrape())
