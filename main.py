#!

""" Fly Bulgarian. Display of flight information. """

from datetime import datetime
import time
import json
import requests
from lxml import html


def load_data(address, headers=None):
    """
    Load html page from url.
    :param address: address of site or request
    :param headers: headers for correct request
    :return: html page as an <html object>
    """

    try:
        page_html = requests.get(address)
        tree = html.fromstring(page_html.content)
        result = tree
        page_html.raise_for_status()
        return result
    except requests.exceptions.ConnectionError:
        print("A Connection error occurred.")
    except requests.exceptions.ReadTimeout:
        print("Read timeout occurred")
    except requests.exceptions.HTTPError as response:
        print("HTTP Error occurred")
        print("Code: {}".format(response))


def get_iata(page):
    """

    :param page:
    :return:
    """

    try:
        form = page.xpath("./body/div[@id='wrapper']/div[@id='content']/"
                          "div[@id='reserve']/form[@id='reserve-form']")[0]
        options = form.xpath("./dl/dd[@class='double']/"
                             "select[@id='departure-city']/"
                             "option/@value")[1:]
        result = tuple(options)
        return result
    except (AttributeError, IndexError):
        print("Incorrect result of load_data(address) function")


def input_data(page):
    """"""

    wrong_data = True
    code_message = "must be correct IATA-code and conform to upper-case"
    date_message = "must be correct date format: DD.MM.YYYY"

    iata_codes = get_iata(page)
    print(iata_codes)

    while wrong_data:
        incorrect_value = []
        dep_iata = input('Enter a departure city IATA-code: ')
        arr_iata = input('Enter a arrival city IATA-code: ')

        try:
            dep_date = input('Enter a departure date in'
                             ' format DD.MM.YYYY): ')
            dep_date = datetime.strptime(dep_date, "%d.%m.%Y")\
                .date().strftime("%d.%m.%Y")
            # arrival_date = input('Enter a arrival date in format DD.MM.YYYY: ')
        except ValueError:
            incorrect_value.append((dep_date, date_message))
        # print(type(dep_date))
        # depar_iata = 'BOJ'
        # arrive_iata = 'BLL'
        # dep_date = '08.07.2019'
        if (dep_iata not in iata_codes) or \
                (not dep_iata.isupper()):
            incorrect_value.append((dep_iata, code_message))

        if (arr_iata not in iata_codes) or \
                (not arr_iata.isupper()):
            incorrect_value.append((arr_iata, code_message))

        if not incorrect_value:
            wrong_data = False
        else:
            for bug in incorrect_value:
                print("Incorrect value: {} {}".format(bug[0], bug[1]))

    return dep_iata, arr_iata, dep_date


def get_search_page(values):
    """"""

    url = ("http://www.flybulgarien.dk/en/search?lang=2&departure-city={}&"
           "arrival-city={}&reserve-type=&departure-date={}&"
           "adults-children=1&search=Search%21".format(values[0],
                                                       values[1], values[2]))
    result = load_data(url)
    return result


def one_way_flight(page):
    """"""

    index = 1
    result = []

    iframe = page.xpath("./body/div[@id='wrapper']/div[@id='content']/"
                        "div[@id='inner-page']/"
                        "div[@class='text-content']/iframe")[0]

    document = iframe.get('src')
    oneway_fly = load_data(document)

    tr_table = oneway_fly.xpath("./body/form[@id='form1']/"
                                "div[@style='padding: 10px;']/"
                                "table[@id='flywiz']/child::*")[0]
    table_tr = tr_table.xpath("./td/table[@id='flywiz_tblQuotes']")[0]

    td = table_tr.xpath("./tr[@class='selectedrow']|"
                        "./tr[@class='notselrow']")

    for tr in enumerate(td):
        if tr[0] % 2 == 0:
            fly_date = tuple(tr[1].xpath("./td/text()")[0:3])
            dep_time = datetime.strptime(fly_date[0] + fly_date[1],
                                         "%a, %d %b %y%H:%M")

            arr_time = datetime.strptime(fly_date[0] + fly_date[2],
                                         "%a, %d %b %y%H:%M")
        else:
            price = tr[1].xpath("./td/text()")[0][-10:]
        if index % 2 == 0:
            result.append((fly_date[0], dep_time, arr_time, price))
        index += 1
    return result


def get_data():
    """"""

    one_way = True
    result = []
    if one_way:
        fly_data = one_way_flight(search_page)

    for flight in fly_data:
        flight_dict = {"Date": flight[0],
                       "Departure time": flight[1].strftime("%H:%M"),
                       "Arrival time": flight[2].strftime("%H:%M"),
                       "Flight time": str(flight[2] - flight[1])[-7:],
                       "Class": "Standard",
                       "Price": flight[3]
                       }
        result.append(flight_dict)
    return json.dumps(result, indent=4)


if __name__ == '__main__':
    url = "http://www.flybulgarien.dk/en/"
    data = load_data(url)
    values = input_data(data)
    start_time = time.perf_counter()
    search_page = get_search_page(values)
    print(get_data())
    print(time.perf_counter() - start_time, "seconds")
