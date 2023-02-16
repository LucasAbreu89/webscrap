def scrap(x, y=None):
    """A function that scrapes a website called imovelweb and returns a csv file with some property characteristics.

    Args:
        x (int): First page to scrape. If y is not specified, this argument is treated as a single page input.
        y (int, optional): Last page to scrape (not included in the range of pages to scrape). 
                           If specified, pages x to y-1 will be scraped.

    Returns:
        A real.csv file, including some property characteristics.
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import numpy as np
    import pandas as pd
    import re
    import csv
    import time
    import os

    if x == 0:
        raise ValueError("The value of x cannot be zero.")

    if y is None:
        # Single page input
        page_range = [x]
    else:
        # Multiple pages input
        page_range = range(x, y)

    url_template = "https://www.imovelweb.com.br/apartamentos-venda-belo-horizonte-mg-pagina-{}.html"

    # Create a new Options object for configuring the Chrome driver
    option = Options()

    # Set the window size of the browser to 1920x1080 pixels
    option.add_argument("--window-size=1920,1080")

    # Disable GPU acceleration to improve performance
    option.add_argument("--disable-gpu")

    # Disable any installed browser extensions to avoid potential conflicts
    option.add_argument("--disable-extensions")

    # Disable the use of automation extensions, which could interfere with website behavior
    option.add_argument('--disable-useAutomationExtension')

    # Specify a direct connection to the internet, bypassing any proxy settings
    option.add_argument("--proxy-server='direct://'")
    option.add_argument("--proxy-bypass-list=*")

    # Start the browser maximized to fill the screen
    option.add_argument("--start-maximized")

    # Run the browser in headless mode, meaning without a visible user interface
    option.add_argument("--headless")

    # Set the User-Agent header of the browser to mimic a Windows 10 desktop machine running Chrome 87
    option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)" +
                        "AppleWebKit/537.36 (KHTML, like Gecko)"+"Chrome/87.0.4280.141 Safari/537.36")

    servico = Service(ChromeDriverManager().install())

    for page_num in page_range:
        url = url_template.format(page_num)
        driver = webdriver.Chrome(service=servico, options=option)
        driver.get(url)

        time.sleep(6)
        for i in range(17):
            driver.execute_script("window.scrollBy(0, 350)")
            time.sleep(0.5)

        # finding the elements
        imgResults = driver.find_elements(
            By.CSS_SELECTOR, '[data-qa="posting PROPERTY"] .flickity-slider img:first-child')
        item_end = driver.find_elements(
            By.CSS_SELECTOR, '[data-qa="posting PROPERTY"] [data-qa="POSTING_CARD_LOCATION"]')
        item_add = driver.find_elements(By.CLASS_NAME, 'sc-ge2uzh-0')
        item_ban = driver.find_elements(
            By.CSS_SELECTOR, '[data-qa="posting PROPERTY"] [data-qa="POSTING_CARD_FEATURES"]')
        item_cond = driver.find_elements(By.CLASS_NAME, 'sc-12dh9kl-0')

        # cleaning / organizing lists
        add = [str(element.text) for element in item_add]
        ban1 = [element.text for element in item_ban]
        ban1 = [element.replace("\n", " ") for element in ban1]
        cond1 = [str(element.text) for element in item_cond]
        cond1 = [x.replace("\n", " ").replace("R$", "").replace(
            "Condominio", "").replace(".", "").strip() for x in cond1]

        # creating a list of each element we want to extract
        prices = [int(row.split()[0]) for row in cond1]
        condos = [int(row.split()[1]) if len(row.split())
                  == 2 else np.nan for row in cond1]
        ender = [str(element.text.split(",")[0]) for element in item_end]
        add1 = [x.split(',')[0] if ',' in x and len(x.split(','))
                >= 2 else (np.nan if x == '' else x) for x in add]
        area = [x.split('m²')[1].strip().split()[0] for x in ban1 if 'm²' in x]
        bedrooms = [re.search(r'(\d+) quartos', x).group(1)
                    if 'quartos' in x else np.nan for x in ban1]
        baths = [re.search(r'(\d+)\sban', x).group(1)
                 if 'ban' in x else np.nan for x in ban1]
        parking = [re.search(r'(\d+)\svagas', x).group(1)
                   if 'vagas' in x else np.nan for x in ban1]
        src_list = [img.get_attribute('src') for img in imgResults]

        # creating a header for my list
        header = ("price (R$)", "condo (R$)", "district", "adress",
                  "area (m²)", "bedroom", "bathrooms", "parkings", "url")

        # creating a list of tuples
        total = list(zip(prices, condos, ender, add1, area,
                     bedrooms, baths, parking, src_list))

        # create a list with my header
        result = [header] + total

        # Define the path to the CSV file
        file_path = 'real.csv'

        # If the CSV file does not exist, create it with the header
        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)

        # Write the new tuples to the CSV file
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for row in total:
                writer.writerow(row)

        check = pd.read_csv("real.csv")

        check.drop_duplicates(inplace=True)
        check["price (R$)"] = check["price (R$)"].astype(float)
        check["area (m²)"] = check["area (m²)"].astype(float)

        check.to_csv('real.csv', index=False)
        driver.quit()

    print("Time to look at your csv file")
