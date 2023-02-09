from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import re
import csv
import pandas as pd


def scrap(x, y):
    """A function that scrap a website called imovelweb and returns a csv file with some property characteristics.

    Args:
        x (int): First page to scrap
        y (int): Last page to scrap

    Returns:
        A real.csv file, including the price, number of bathrooms, number of bedrooms, area, parking and adress of a property
    """
    url_template = "https://www.imovelweb.com.br/apartamentos-venda-belo-horizonte-mg-pagina-{}.html"
    header = ("price", "district", "bedroom", "area", "bathrooms", "parkings")

    preco = []
    bedrooms = []
    area = []
    baths = []
    parking = []
    ender = []

    for page_num in range(x, y):
        url = url_template.format(page_num)
        UserAgent = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(UserAgent)
        data = BeautifulSoup(html, 'html.parser')
        # do your data processing here

        item_preco = data.find_all(
            attrs={"data-qa": "posting PROPERTY", 'data-qa': 'POSTING_CARD_PRICE'})
        item_end = data.find_all(attrs={"data-qa": "posting PROPERTY",
                                 "class": "sc-ge2uzh-2 hWApJB", "data-qa": "POSTING_CARD_LOCATION"})
        item_ban = data.find_all(attrs={"data-qa": "posting PROPERTY",
                                 "class": "sc-1uhtbxc-0 cIDnkN", "data-qa": "POSTING_CARD_FEATURES"})

        if len(item_preco) > 0:
            first_item = item_preco[0]
            item_text = first_item.get_text()

        else:
            print("No elements with the specified class found.")

        for element in item_preco:
            item1 = int(element.text.replace("R$", "").replace(".", ""))
            preco.append(item1)

        for element in item_end:
            item2 = str(element.text.split(",")[0])
            ender.append(item2)

        for tag in item_ban:
            text = tag.text
            match = re.search(r'(\d+) quartos', text)
            if match:
                beds = match.group(1)
                bedrooms.append(beds)

            match_m2 = re.findall(r'(\d+)\sm²', text)
            if match_m2:
                area.append(match_m2[1])

            match_baths = re.search(r'(\d+)\sban', text)
            if match_baths:
                bath = match_baths.group(1)
                baths.append(bath)

            match_parking = re.search(r'(\d+)\svagas', text)
            if match_parking:
                park = match_parking.group(1)
                parking.append(park)

        total = list(zip(preco, ender, bedrooms, area, baths, parking))
        unique = set(total)

        existing_tuples = set()

        try:
            with open('real.csv', 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # skip the header
                existing_tuples.update(tuple(row) for row in reader)
        except FileNotFoundError:
            with open('real.csv', 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)

        # Write new tuples to the csv file
        with open('real.csv', 'a', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in unique:
                if tuple(row) not in existing_tuples:
                    writer.writerow(row)
                    existing_tuples.add(tuple(row))

        check = pd.read_csv("real.csv")
        check['district'] = check['district'].astype(str)
        check = check.astype({"price": float, "bedroom": float,
                             "area": float, "bathrooms": float, "parkings": float})

        check.drop_duplicates(inplace=True)
        check.to_csv('real.csv', index=False)
