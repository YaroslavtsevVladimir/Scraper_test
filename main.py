#!

""" Fly Bulgarian. Display of flight information. """

from datetime import datetime
import json
import requests
from lxml import html


def load_data(address, headers=None):
    """
    Load html page from url.
    :param address: url
    :param headers: headers for correct GET request
    :return: html page as an <html object>
    """

    try:
        page_html = requests.get(address)
        tree = html.fromstring(page_html.content.decode("utf-8"))
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
        option = form.xpath("./dl/dd[@class='double']/"
                            "select[@id='departure-city']/"
                            "option/@value")[1:]
        result = tuple(option)
        return result
    except AttributeError:
        print("Incorrect result of load_data(address) function")


def input_data():
    """"""

    wrong_data = True
    code_message = "must be correct IATA-code and conform to upper-case"
    date_message = "must be correct date format: DD.MM.YYYY"
    html_page = load_data(url)
    iata_codes = get_iata(html_page)
    print(iata_codes)

    while wrong_data:
        incorrect_value = []
        # dep_iata = input('Enter a departure city IATA-code: ')
        # arrival_iata = input('Enter a arrival city IATA-code: ')

        # try:
            # dep_date = input('Enter a departure date in'
            #                  ' format DD.MM.YYYY): ')
            # arrival_date = input('Enter a arrival date in format DD.MM.YYYY: ')
            # dep_date = datetime.strptime(dep_date, "%d.%m.%Y")\
            #     .date().strftime("%d.%m.%Y")
        # except ValueError:
        #     incorrect_value.append((dep_date, date_message))
        dep_iata = 'CPH'
        arr_iata = 'VAR'
        dep_date = '02.07.2019'
        if (dep_iata not in iata_codes) or\
                (not dep_iata.isupper()):
            incorrect_value.append((dep_iata, code_message))

        if (arr_iata not in iata_codes) or\
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
    data = load_data(url)
    document = data.xpath("//iframe")[0]
    table = document.get('src')
    d = requests.get(table).content

    print(document)
    print(d)


def get_data():
    pass


if __name__ == '__main__':

    url = "http://www.flybulgarien.dk/en/"

    data = input_data()
    print(data)
    get_search_page(data)
