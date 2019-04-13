
""" Fly Bulgarian. Display of flight information. """

import argparse
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import product, zip_longest
import re
import sys
import requests
from lxml import html

URL = 'https://apps.penguin.bg/fly/quote3.aspx'
REG_IATA = re.compile(r'[A-Z]{3}')
REG_PRICE = re.compile(r'Price:\s{2}(\d{2,3}\.\d{2})( EUR)')


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
                 -arr_date=01.08.2019 -num_seats=3;
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


def send_request(data):
    """
    Load html page from url.

    :param data: data for formation requests.

    :return: html page as an <html object>
    """
    try:
        # A lot of time to read is given due to a long request to the
        # search page.
        request = requests.get(URL, params=data, timeout=(3, 25))
        tree = html.fromstring(request.content)
        request.raise_for_status()
        return tree
    except requests.exceptions.ConnectionError as error:
        sys.exit('Connection Error: {}'.format(error))

    except requests.exceptions.ReadTimeout as error:
        sys.exit('ReadTime Error: {}'.format(error))

    except requests.exceptions.HTTPError as response:
        sys.exit('Code: {}'.format(response))


def input_data():
    """
    User input and validation check. Input continues
    until valid values are entered or enter 'exit' to
    quit.

    :return: dict with data -> (departure IATA-code,
             arrival IATA-code, departure date, arrival date,
             number of seats).
    """
    while True:
        user_input = input('Enter flight details - '
                           'departure city,arrival city,'
                           'departure date,number of seats'
                           '[,arrival date]\nin format '
                           'CPH,BLL,15.07.2019,2[,25.07.2019]'
                           'or enter "exit" ot quit: ')

        if user_input == 'exit':
            raise SystemExit

        data_list_values = tuple(user_input.split(','))

        data_dict_keys = ('dep_city', 'arr_city', 'dep_date',
                          'num_seats', 'arr_date')

        user_data = {key: value for key, value in
                     zip_longest(data_dict_keys, data_list_values)}
        try:
            is_data_valid(user_data)
        except InvalidData as error:
            print(error)
            continue

        return user_data


def is_data_valid(user_data):
    """
    Checked result of input_data() for correctness.
    if data is incorrect, then exception InvalidData is called
    and print the message with information about incorrect value.

    :return: if exception InvalidData is called - message about
             incorrect value,
             else dict -> {'dep_city': 'CPH', 'arr_city': 'VAR',
                           'dep_date': '15.07.2019',
                           'arr_date': '20.07.2019',
                           'num_seats': '2',
                           'dep_date_object': '15.07.2019'}
              for one-way flight 'arr_date': None.
    """
    today = datetime.today().date()
    if any(not user_data[key] for key in ['dep_city', 'arr_city',
                                          'dep_date', 'num_seats']):
        raise InvalidData('No parameters specified.')

    # Valid IATA-code check
    if not REG_IATA.match(user_data['dep_city']) \
            or not REG_IATA.match(user_data['arr_city']):
        raise InvalidData('Incorrect IATA-code. Must consist of three'
                          ' uppercase symbols.')

    # Valid number of seats check
    try:
        num_seats = int(user_data['num_seats'])
        if num_seats not in range(1, 9):
            raise InvalidData('Incorrect numbers of seats. Must be in [1,8]')
    except ValueError:
        raise InvalidData('Incorrect number of seats value. Must be number '
                          'in [1,8]')

    # Valid date check
    try:
        dep_date = datetime.strptime(user_data['dep_date'], '%d.%m.%Y').date()
        user_data['dep_date_object'] = dep_date
        if dep_date < today:
            raise InvalidData('Date should not be less than today.')

        if user_data['arr_date']:
            arr_date = datetime.strptime(user_data['arr_date'],
                                         '%d.%m.%Y').date()
            user_data['arr_date_object'] = arr_date
            if arr_date < dep_date:
                raise InvalidData('Arrival date should not be more than'
                                  ' departure date')

    except ValueError:
        raise InvalidData('Incorrect date format. Must be DD.MM.YYYY.')

    return user_data


def get_search_page(user_data):
    """
    Get search page for parsing flight information.
    Tag <iframe> attribute <src> is used as request.

    :param user_data: result of input_data(page).
                   If Arrival date(values['arr_date') is None -
                   - use request for one-way flight.

    :return: html page as an <html object>
    """
    data = {'ow': '',
            'lang': 'en',
            'depdate': user_data['dep_date'],
            'aptcode1': user_data['dep_city'],
            'aptcode2': user_data['arr_city'],
            'paxcount': user_data['num_seats'],
            'infcount': ''}

    if user_data['arr_date'] is not None:
        data['rt'] = data.pop('ow')
        data.update(rtdate=user_data['arr_date'])

    return send_request(data)


def parse_data(info, price):
    """
    Get information about date, time, airports
    and price for flights. For this called functions:
    parse_date(info), parse_cities(info), parse_price(price).

    :param info: table row containing date, time
                 and airports.
    :param price: table row containing price.

    :return: parse dict -> {'dep_city': dep_city,
                            'arr_city': arr_city,
                            'dep_date': dep_date,
                            'arr_date': arr_date,
                            'duration': duration,
                            'price': price,
                            'currency': currency}
    """
    dep_city, arr_city = parse_cities(info)

    dep_date, arr_date = parse_date(info)
    duration = arr_date - dep_date

    price, currency = parse_price(price)

    return {'dep_city': dep_city,
            'arr_city': arr_city,
            'dep_date': dep_date,
            'arr_date': arr_date,
            'duration': duration,
            'price': price,
            'currency': currency}


def parse_date(info):
    """
    Get information about flights date.

    :param info: table row containing date, time
                 and airports.

    :return: tuple -> (dep_date, arr_date)
    """
    fly_date = info.xpath("./td[2]/text()")[0]
    dep_time = info.xpath("./td[3]/text()")[0]
    arr_time = info.xpath("./td[4]/text()")[0]

    dep_date = datetime.strptime(fly_date + dep_time,
                                 "%a, %d %b %y%H:%M")
    arr_date = datetime.strptime(fly_date + arr_time,
                                 "%a, %d %b %y%H:%M")

    # If arrival time is after midnight
    if arr_date < dep_date:
        arr_date += timedelta(days=1)

    return dep_date, arr_date


def parse_cities(info):
    """
    Get information about flights date.

    :param info: table row containing date, time
                 and airports.

    :return: tuple -> (dep_city, arr_city)
    """
    dep_airport = info.xpath("./td[5]/text()")[0]
    arr_airport = info.xpath("./td[6]/text()")[0]

    dep_city = REG_IATA.search(dep_airport).group()
    arr_city = REG_IATA.search(arr_airport).group()

    return dep_city, arr_city


def parse_price(price_element):
    """
    Get information about flights price.

    :param price_element: table row containing price.

    :return: tuple -> (float(price), currency)
    """
    price_string = price_element.xpath(
        './td[contains(text(), "Price")]/text()'
    )[0]

    price = REG_PRICE.search(price_string).group(1)
    currency = REG_PRICE.search(price_string).group(2)
    return float(price), currency


def parse_results(search_page, user_data):
    """
    Get flight information for entered data in input_data(page).
    Create dict with nested lists with <tr> tags witch
    contain information about city, date and price.

    :param search_page: result of get_search_page(values).
    :param user_data: flight parameters entered by the user.

    :return: function finalize_results(user_data, flights).
    """
    info_xpath = './/table//tr[contains(@id, "_{}inf")]'
    price_xpath = './/table//tr[contains(@id, "_{}prc")]'

    flights = defaultdict(list)
    indexes = [0] if not user_data['arr_date'] else [0, 1]

    for i, key in zip(indexes, ['r', 'ir']):
        infos = search_page.xpath(info_xpath.format(key))
        prices = search_page.xpath(price_xpath.format(key))

        if not infos or not prices:
            raise NoResultException('No {} flights found.'.format(
                {0: 'outbound', 1: 'inbound'}[i]))

        for info, price in zip(infos, prices):
            flights[i].append(parse_data(info, price))

    return finalize_results(user_data, flights)


def check_flight(user_data, flight):
    """
    Checked for coincidence of entered airports and dates taken
    from the search page. If no match, AssertionError is called.

    :param user_data: flight parameters entered by the user.
    :param flight: dict with flights data.
    """
    count = 1 if not user_data['arr_date'] else 2
    assert count == len(flight)

    assert all([
        user_data['dep_date_object'] == flight[0]['dep_date'].date(),
        user_data['dep_city'] == flight[0]['dep_city'],
        user_data['arr_city'] == flight[0]['arr_city']
    ])

    if user_data['arr_date']:
        assert all([
            user_data['arr_date_object'] == flight[1]['dep_date'].date(),
            user_data['arr_city'] == flight[1]['dep_city'],
            user_data['dep_city'] == flight[1]['arr_city'],
            flight[1]['dep_date'] > flight[0]['dep_date']
        ])


def finalize_results(user_data, flights):
    """
    Generates flights data and sort by price.

    :param user_data: flight parameters entered by the user.
    :param flights: dict with flights data.

    :return: sorted list with
    """
    num_seats = int(user_data['num_seats'])
    final_results = []

    for flight in product(*flights.values()):
        try:
            check_flight(user_data, flight)
        except AssertionError:
            continue

        flight_dict = {}
        for header, data in zip(['Going out:', 'Coming back:'], flight):

            data.update(
                {'dep_date_sec': data['dep_date'].strftime('%d.%m.%Y %H:%M'),
                 'arr_date_sec': data['arr_date'].strftime('%d.%m.%Y %H:%M'),
                 'duration': str(data['duration'])[:-3]})

            flight_dict[header] = ('Departure_city: {dep_city},'
                                   ' Arrival_city: {arr_city},'
                                   ' Departure_date: {dep_date_sec},'
                                   ' Arrival_date: {arr_date_sec},'
                                   ' Duration: {duration}').format(**data)

        flight_dict['Price:'] = str(
            sum(d['price'] * num_seats for d in flight))\
            + flight[0]['currency']

        final_results.append(flight_dict)

    return sorted(final_results, key=lambda d: d['Price:'].split()[0])


def print_results(results):
    """
    Data processing and formation.

    :param results: result of finalize_results(user_data, flights).

    :return: flight information:
     - one-way flight:
        Found results:
        Going out: Dep_city: CPH, Arr_city: VAR, Dep_date: 2019-07-13 21:50:00,
         Arr_date: 2019-07-14 01:40:00
        Price: 320.0 EUR;
     - return flight:
        Going out: Departure_city: BLL, Arrival_city: BOJ,
         Departure_date: 2019-07-15 18:45, Arrival_date: 2019-07-15 22:45,
          Duration: 4:00
        Coming back: Departure_city: BOJ, Arrival_city: BLL,
         Departure_date: 2019-07-29 16:00, Arrival_date: 2019-07-29 17:50,
          Duration: 1:50
        Price: 768.0 EUR.
     Flight results sorted by price.
    """
    if results:
        print('Found results: ')
        for result in results:
            for key, value in result.items():
                print(key, value)
            print('\n')
    else:
        print('No flights found for requested data.')


def scrape():
    """
    Main function. Call other functions to collect and
    generates flight information.
    If function get_args is called without arguments, then called
    InvalidData and the data are entered by the user.

    :return: information about flights or report that no results
             were found for this data.
    """
    user_data = get_args()
    try:
        is_data_valid(user_data)
    except InvalidData as error:
        print('Input data incorrect. {} Please try again.'.format(error))
        user_data = input_data()

    search_page = get_search_page(user_data)
    try:
        results = parse_results(search_page, user_data)
    except NoResultException as error:
        print(error)
    else:
        print_results(results)


if __name__ == '__main__':
    scrape()
