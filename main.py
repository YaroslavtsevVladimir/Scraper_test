#!

""" Fly Bulgarian. Display of flight information. """


from datetime import datetime
import time
import json
import re
from itertools import product
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
        raise requests.exceptions.ConnectionError("A Connection error "
                                                  "occurred.")
    except requests.exceptions.ReadTimeout:
        raise requests.exceptions.ReadTimeout("Read timeout occurred")
    except requests.exceptions.HTTPError as response:
        raise requests.exceptions.HTTPError("Code: {}".format(response))


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
        bug_list = []
        dep_iata = input("Enter a departure city IATA-code: ")
        arr_iata = input("Enter a arrival city IATA-code: ")

        dep_date = input("Enter a departure date in"
                         " format DD.MM.YYYY: ")

        arr_date = input("Enter a arrival date in format DD.MM.YYYY"
                         " or 'skip': ")

        try:
            dep_date = datetime.strptime(dep_date, "%d.%m.%Y")\
                .date().strftime("%d.%m.%Y")

        except ValueError:
            bug_list.append((dep_date, date_message))

        if arr_date != "skip":
            try:
                arr_date = datetime.strptime(arr_date, "%d.%m.%Y") \
                    .date().strftime("%d.%m.%Y")
            except ValueError:
                bug_list.append((arr_date, date_message))

        if (dep_iata not in iata_codes) or \
                (not dep_iata.isupper()):
            bug_list.append((dep_iata, code_message))

        if (arr_iata not in iata_codes) or \
                (not arr_iata.isupper()):
            bug_list.append((arr_iata, code_message))

        if not bug_list:
            wrong_data = False
        else:
            for bug in bug_list:
                print("Incorrect value: {} {}".format(bug[0], bug[1]))

    return dep_iata, arr_iata, dep_date, arr_date


def get_search_page(values):
    """"""

    if values[3] == "skip":

        url = ("http://www.flybulgarien.dk/en/search?lang=2&departure-city={}&"
               "arrival-city={}&reserve-type=&departure-date={}&"
               "adults-children=1&search=Search%21".format(values[0],
                                                           values[1],
                                                           values[2]))
        result = load_data(url)
    else:
        url = ("http://www.flybulgarien.dk/en/search?lang=2&departure-city={}&"
               "arrival-city={}&reserve-type=&departure-date={}&"
               "arrival-date={}&adults-children=1&search=Search%21".format(
                values[0], values[1], values[2], values[3]))

        result = load_data(url)
    return result


def flight_information(page):
    """"""

    index = 1
    out = []
    back = []
    iframe = page.xpath("./body/div[@id='wrapper']/div[@id='content']/"
                        "div[@id='inner-page']/"
                        "div[@class='text-content']/iframe")[0]

    document = iframe.get('src')
    oneway_fly = load_data(document)

    table_tr = oneway_fly.xpath("./body/form[@id='form1']/"
                                "div[@style='padding: 10px;']/"
                                "table[@id='flywiz']/child::*")[0]
    tr_table = table_tr.xpath("./td/table[@id='flywiz_tblQuotes']")[0]

    td = tr_table.xpath("./tr[@class='selectedrow']|"
                        "./tr[@class='notselrow']")

    if not td:
        return "No available flights found."
    else:
        for tr in enumerate(td):
            if tr[0] % 2 == 0:
                fly_date = tuple(tr[1].xpath("./td/text()")[0:4])
                dep_time = datetime.strptime(fly_date[0] + fly_date[1],
                                             "%a, %d %b %y%H:%M")

                arr_time = datetime.strptime(fly_date[0] + fly_date[2],
                                             "%a, %d %b %y%H:%M")
                dep_city = fly_date[3]

            else:
                price = tr[1].xpath("./td/text()")[0]
                reg = re.compile(r'.(\d{3}\.\d{2})( EUR)')
                parse_price = reg.findall(price)

            if index == 1:
                checked = dep_city

            if index % 2 == 0:
                if checked == dep_city:
                    out.append((fly_date[0], dep_time, arr_time, parse_price))
                else:
                    back.append((fly_date[0], dep_time, arr_time, parse_price))
            index += 1

    return out, back


def get_data():
    """"""

    result = []
    fly_data = flight_information(search_page)
    if isinstance(fly_data, str):
        return fly_data
    else:
        if not fly_data[1]:
            for flight in fly_data[0]:
                flight_dict = {"Date": flight[0],
                               "Departure time": flight[1].strftime("%H:%M"),
                               "Arrival time": flight[2].strftime("%H:%M"),
                               "Flight time": str(flight[2] - flight[1])[-7:],
                               "Class": "Standard",
                               "Price": flight[3][0][0] + flight[3][0][1]
                               }
                result.append(flight_dict)
        else:
            combination = product(fly_data[0], fly_data[1])
            for flight in combination:
                print(flight)
                wrong_date = flight[0][1] > flight[1][2]
                if wrong_date:
                    continue
                else:
                    price = str(float(flight[0][3][0][0])
                                + float(flight[1][3][0][0]))
                    flight_dict = {"Departure date": flight[0][0],
                                   "Arrival date": flight[1][0],
                                   "Class": "Standard",
                                   "Price": price + flight[0][3][0][1]}
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
