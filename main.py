
""" Fly Bulgarian. Display of flight information. """

import argparse
from datetime import datetime
from itertools import product, zip_longest
import json
import re
import requests
from lxml import html

URL = 'https://apps.penguin.bg/fly/quote3.aspx'
VALID_IATA = re.compile(r'^[A-Z]{3}$')
REG_PRICE = re.compile(r'Price:\s{2}(\d{2,3}\.\d{2})( EUR)')
REG_IATA = re.compile(r'[A-Z]{3}')


class NoResultException(Exception):
    """ Error for no flight result. """


class InvalidData(Exception):
    """ Error for incorrect user input. """


def get_args():
    """
    Get named command line arguments.
    flight parameters: departure IATA-code,
                   Arrival IATA-code, Departure date, Arrival Date,
                   number of seats.
    For example: -dep_city=CPH -arr_city=BOJ -dep_date=01.07.2019
                 -arr_date=01.08.2019 -num_seats=1;
                 -dep_city=CPH -arr_city=BOJ -dep_date=01.07.2019
                  -num_seats=1.
    :return: dict with arguments -> {'-dep_city': 'CPH',
                                     '-arr_city': 'VAR',
                                     '-dep_date': '02.07.2019',
                                     '-arr_date': '15.07.2019',
                                     '-num_seats': 2}
    """

    parser = argparse.ArgumentParser(description='Fly Bulgarian scraping.')
    parser.add_argument('-dep_city', type=str, help='Departure city')
    parser.add_argument('-arr_city', type=str, help='Arrival city')
    parser.add_argument('-dep_date', type=str, help='Departure date')
    parser.add_argument('-arr_date', type=str, help='Arrival date')
    parser.add_argument('-num_seats', type=int, help='Number of seats')
    arguments = parser.parse_args()
    args_dict = vars(arguments)
    return args_dict


def send_request(*args):
    """
    Load html page from url.

    :param args: request type or url,
                 headers and data

    :return: html page as an <html object>
    """

    try:
        if args[0] != "POST":
            request = requests.get(args[0], params=args[1], timeout=(3, 10))
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


def input_data():
    """
    User input and validation check. Input continues
    until valid values are entered.

    :return: dict with data -> (departure IATA-code,
             arrival IATA-code, departure date[, arrival date],
             number of seats)
    """

    while True:
        user_input = input("Enter flight details - "
                           "departure city,arrival city,"
                           "departure date,number of seats"
                           "[,arrival date]\n in format "
                           "CPH,BLL,15.04.2019,2: ")

        data_list = tuple(user_input.split(','))

        data_dict_keys = ('dep_city', 'arr_city', 'dep_date',
                          'num_seats', 'arr_date')

        user_data = {key: value for key, value in
                     zip_longest(data_dict_keys, data_list)}
        try:
            is_data_valid(user_data)
        except InvalidData as error:
            print(error)
            continue
        except KeyError:
            print('Not enough data.')
            continue

        return user_data


def is_data_valid(user_data):
    """
    Checked result of input_data() for correctness.
    Result of iata_code(page) and get_available_date(iata_codes)
    are used to validate user input.
    if data is incorrect, then exception InvalidData is called
    and print the message with information about incorrect value.

    :return: if exception InvalidData is called - message about
             incorrect value,
             else dict -> {"dep_city": "CPH", "arr_city": "VAR",
                           "dep_date": '15.07.2019' ,
                           "arr_date": "20.07.2019",
                           "num_seats": "2"}
              for one-way flight "arr_date": None.
    """

    if any(not user_data[key] for key in ['dep_city', 'arr_city',
                                          'dep_date', 'num_seats']):
        raise InvalidData('No parameters specified.')

    # Valid IATA-code check
    if not VALID_IATA.match(user_data['dep_city']) \
            or not VALID_IATA.match(user_data['arr_city']):
        raise InvalidData('Incorrect IATA-code. Must consist of three'
                          'uppercase symbols.')

    # Valid number of seats check
    num_seats = int(user_data['num_seats'])
    if num_seats not in range(1, 9):
        raise InvalidData('Incorrect numbers of seats. Must be in [1,8]')

    # Valid date check
    try:
        dep_date = datetime.strptime(user_data['dep_date'], '%d.%m.%Y').date()

        if user_data['arr_date']:
            arr_date = datetime.strptime(user_data['arr_date'],
                                         '%d.%m.%Y').date()
            if arr_date < dep_date:
                raise InvalidData('Arrival date should not be more than'
                                  ' departure date')

    except ValueError:
        raise InvalidData('Incorrect date format. Must be DD/MM/YYYY,'
                          'and date should not be greater than and.')

    return user_data


def get_search_page(values):
    """
    Get search page for parsing flight information.
    Tag <iframe> attribute <src> is used as request.

    :param values: result of input_data(page).
                   If Arrival date(values["arr_date") is None -
                   - use request for one-way flight.

    :return: html page as an <html object>
    """

    data = {'ow': '',
            'lang': 'en',
            'depdate': values['dep_date'],
            'aptcode1': values['dep_city'],
            'aptcode2': values['arr_city'],
            'paxcount': values['num_seats'],
            'infcount': ''}

    if values['arr_date'] is not None:
        data['rt'] = data.pop('ow')
        data.update(rtdate=values['arr_date'])

    return send_request(URL, data)


def parse_data(info, price):
    """

    :param info:
    :param price:
    :return:
    """

    fly_date = info.xpath("./td[2]/text()")[0]
    dep_time = info.xpath("./td[3]/text()")[0]
    arr_time = info.xpath("./td[4]/text()")[0]
    dep_airport = info.xpath("./td[5]/text()")[0]
    arr_airport = info.xpath("./td[6]/text()")[0]

    dep_date = datetime.strptime(fly_date + dep_time,
                                 "%a, %d %b %y%H:%M")
    arr_date = datetime.strptime(fly_date + arr_time,
                                 "%a, %d %b %y%H:%M")

    dep_iata = REG_IATA.search(dep_airport).group()
    arr_iata = REG_IATA.search(arr_airport).group()

    price_elem = price.xpath('./td[contains(text(), "Price")]/text()')[0]

    parse_price = REG_PRICE.search(price_elem).group(1)
    currency = REG_PRICE.search(price_elem).group(2)

    result = {'dep_city': dep_iata,
              'arr_city': arr_iata,
              'dep_date': dep_date,
              'arr_date': arr_date,
              'price': (float(parse_price), currency)}

    return result


def get_flight_information(search_page, user_data):
    """
    Get flight information for entered data in input_data(page).
    Create going_out and coming_back lists with <tr> tags for
    Going Out and Coming Back flights.

    :param search_page: result of get_search_page(values)
    :param user_data: flight parameters entered by the user

    :return: For one-way - one_way_flight(going_out)
             For return - return_flight(combination)
             If no information - return "No available flights found."
    """

    try:
        flights = [[], []] if user_data['arr_date'] else [[]]
        outbound_info = search_page.xpath('.//table//tr[contains(@id,'
                                          ' "_rinf")]')
        outbound_prices = search_page.xpath('.//table//tr[contains(@id,'
                                            ' "_rprc")]')

        if not outbound_info:
            raise NoResultException('No outbound flights')

        for info, price in zip(outbound_info, outbound_prices):
            flights[0].append(parse_data(info, price))

    except NoResultException:
        return 'No outbound flights'

    try:
        if user_data['arr_date']:
            inbound_info = search_page.xpath('.//table//tr[contains(@id,'
                                             ' "irinf")]')
            inbound_prices = search_page.xpath('.//table//tr[contains(@id,'
                                               ' "irprc")]')

            if not inbound_info:
                raise NoResultException('No inbounds')

            for info, price in zip(inbound_info, inbound_prices):
                flights[1].append(parse_data(info, price))
    except NoResultException:
        return 'No inbound flights'

    combination = product(*flights)
    return combination


def data_generation(fly_data, user_data):
    """
    Data processing and formation in json format.

    :param fly_data: result of parse_data(info, price)
    :param user_data: flight parameters entered by the user

    :return: if get_flight_information(search_page) return
    "No available flights found." or no valid dates for
     return flight - return "No available flights found."
     else return flight information in json format:
     - one-way flight:
        [
            {
                'Date': 'Sat, 06 Jul 19',
                'Departure time': '21:50',
                'Arrival time': '01:40',
                'Flight time': '3:50:00',
                'Price': '160.00 EUR'
            }
        ];
     - return flight:
        [
            {
                'Going out': 'CPH - VAR',
                'Departure date': 'Tue, 02 Jul 19 21:50',
                'Coming back': 'BOJ - BLL',
                'Arrival date': 'Mon, 22 Jul 19 16:00',
                'Price': '379.0 EUR'
            }
        ].
     Return flight results sorted by price.
    """

    if user_data['arr_date']:
        fly_dict_keys = ('Going out', 'Departure date',
                         'Coming back', 'Arrival date',
                         'Price')

        fly_dict_values = (
            ('{} - {}'.format(flight[0]['dep_city'], flight[0]['arr_city']),
             flight[0]['dep_date'].strftime('%a, %d %b %y %H:%M'),
             '{} - {}'.format(flight[1]['dep_city'], flight[1]['arr_city']),
             flight[1]['dep_date'].strftime('%a, %d %b %y %H:%M'),
             str(flight[0]['price'][0] + flight[1]['price'][0])
             + flight[0]['price'][1]) for flight in fly_data)
    else:
        fly_dict_keys = ('Date', 'Departure time', 'Arrival time',
                         'Flight time', 'price')

        fly_dict_values = (
            (flight[0]['dep_date'].strftime('%a, %d %b %y'),
             flight[0]['dep_date'].strftime('%H:%M'),
             flight[0]['arr_date'].strftime('%H:%M'),
             str(flight[0]['arr_date'] - flight[0]['dep_date'])[-7:],
             str(flight[0]['price'][0])
             + flight[0]['price'][1]) for flight in fly_data)

    flight_list = ({key: value for key, value in zip(fly_dict_keys, values)}
                   for values in fly_dict_values)

    result = sorted(flight_list, key=lambda price_key:
                    max(price_key.items()))
    result = json.dumps(result, indent=4)
    return result


def scrape():
    """
    Main function. Call other functions and
    generates flight information in json format.
    If function is called with arguments **kwargs, then they are
    passed to the get_search_request(values), else called input_data().

    :return: information about flights in json format or
             "No available flights found."
    """

    user_data = get_args()
    try:
        is_data_valid(user_data)
    except InvalidData as error:
        print('Input data incorrect. {} Please try again.'.format(error))
        user_data = input_data()

    search_page = get_search_page(user_data)
    flights = get_flight_information(search_page, user_data)
    if isinstance(flights, str):
        result = flights
    else:
        result = data_generation(flights, user_data)
    return result


if __name__ == '__main__':
    print(scrape())
