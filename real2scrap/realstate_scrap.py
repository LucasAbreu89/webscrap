def scrap(x, y=None, url_type="normal"):
    """A function that scrapes a website called imovelweb and returns a csv file with some property characteristics.

    Args:
        x (int): First page to scrape. If y is not specified, this argument is treated as a single page input.
        y (int, optional): Last page to scrape (not included in the range of pages to scrape).
                           If specified, pages x to y-1 will be scraped.
        url_type (str, optional): Type of URL template to use. "normal" for normal URL or "last-day" for last day URL.

    Returns:
        A csv file and feeds a database in supabase.
    """

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from supabase import create_client
    from datetime import datetime, timedelta
    import numpy as np
    import pandas as pd
    import re
    import csv
    import time
    import json
    import os
    from dotenv import load_dotenv

    load_dotenv()

    url_supa = os.environ.get("SUPABASE_URL")
    key_supa = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url_supa, key_supa)

    if x == 0:
        raise ValueError("The value of x cannot be zero.")

    if y is None:
        # Single page input
        page_range = [x]
    else:
        # Multiple pages input
        page_range = range(x, y)

    if url_type == "normal":
        url_template = "https://www.imovelweb.com.br/apartamentos-venda-belo-horizonte-mg-pagina-{}.html"
    elif url_type == "last-day":
        url_template = "https://www.imovelweb.com.br/apartamentos-venda-belo-horizonte-mg-publicado-no-ultimo-dia-pagina-{}.html"
    else:
        raise ValueError("Invalid url_type. Must be 'normal' or 'last-day'.")

    url_list = [url_template.format(page) for page in page_range]

    base_url = "https://www.imovelweb.com.br"

    # Get the current datetime in UTC
    date1 = (datetime.utcnow() - timedelta(hours=3)
             ).strftime("%Y-%m-%dT%H:%M:%S")

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
        start_time = time.time()
        url = url_template.format(page_num)
        driver = webdriver.Chrome(service=servico, options=option)
        driver.get(url)

        time.sleep(6)
        for i in range(17):
            driver.execute_script("window.scrollBy(0, 350)")
            time.sleep(0.5)

        # finding the elements
        scrap_img = driver.find_elements(
            By.CSS_SELECTOR, '[data-qa="posting PROPERTY"] .flickity-slider img:first-child')
        scrap_location = driver.find_elements(
            By.CSS_SELECTOR, '[data-qa="posting PROPERTY"] [data-qa="POSTING_CARD_LOCATION"]')
        scrap_location2 = driver.find_elements(By.CLASS_NAME, 'sc-ge2uzh-0')
        scrap_features = driver.find_elements(
            By.CSS_SELECTOR, '[data-qa="posting PROPERTY"] [data-qa="POSTING_CARD_FEATURES"]')
        scrap_condo = driver.find_elements(By.CLASS_NAME, 'sc-12dh9kl-0')
        scrap_link = driver.find_elements(
            By.CSS_SELECTOR, '[data-qa="posting PROPERTY"]')

        # cleaning / organizing lists
        address = [str(element.text) for element in scrap_location2]
        features1 = [element.text for element in scrap_features]
        features1 = [element.replace("\n", " ") for element in features1]
        condo1 = [str(element.text) for element in scrap_condo]
        condo1 = [x.replace("\n", " ").replace("R$", "").replace(
            "Condominio", "").replace(".", "").strip() for x in condo1]

        # creating a list of each element we want to extract
        prices_brl = [int(row.split()[0]) if len(row.split()) >= 1 and row.split()[
            0].isdigit() else None for row in condo1]
        condos_brl = [int(row.split()[1]) if len(row.split()) == 2 and row.split()[
            1].isdigit() else None for row in condo1]
        district_list = [str(element.text.split(",")[0])
                         if element.text else None for element in scrap_location]
        address_list = [x.split(',')[0] if ',' in x and len(x.split(','))
                        >= 2 else x if x else None for x in address]
        area_list = [x.split('m²')[1].strip() if x.count('m²') > 1 else (
            x.split('m²')[0] + 'm²' if 'm²' in x else np.nan) for x in features1]
        area_list = [x.split()[0].replace('m²', '').strip() for x in area_list]
        bedrooms_list = [re.search(r'(\d+) quartos', x).group(1)
                         if 'quartos' in x else None for x in features1]
        baths_list = [re.search(r'(\d+)\sban', x).group(1)
                      if 'ban' in x else None for x in features1]
        parking_list = [int(re.search(r'(\d+)\svagas', x).group(1))
                        if 'vagas' in x else 0 for x in features1]
        src_list = [img.get_attribute('src') if img.get_attribute(
            'src') else None for img in scrap_img]
        full_links = [
            base_url + element.get_attribute("data-to-posting") for element in scrap_link]

        # creating a header for my list
        header = ("price(R$)", "condo(R$)", "district", "address", "area(m²)",
                  "bedroom", "bathrooms", "parkings", "url(image)", "url(apt)")

        # creating a list of tuples
        total = list(zip(prices_brl, condos_brl, district_list, address_list, area_list,
                     bedrooms_list, baths_list, parking_list, src_list, full_links))

        unique_total = []
        # iterate over each tuple in the total list
        for row in total:
            # check if the row is already in the unique_total list
            if row not in unique_total:
                # if not, append the row to the unique_total list
                unique_total.append(row)

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
            for row in unique_total:
                writer.writerow(row)

        check = pd.read_csv("real.csv")

        # check.drop_duplicates(inplace=True)
        check["price(R$)"] = check["price(R$)"].astype(float)
        check["area(m²)"] = check["area(m²)"].astype(float)
        check['parkings'] = check['parkings'].astype('Int64')

        check.to_csv('real.csv', index=False)

        end_time = time.time()
        diference_time = end_time - start_time

        print(f"page {page_num} was scraped in {round(diference_time)} seconds")
        driver.quit()

    check1 = pd.read_csv("real.csv")

    # Get existing IDs in the table
    existing_ids = supabase.table("data_scrap").select("id").execute().data

    # Convert the IDs to a set for efficient membership testing
    existing_ids = set([row["id"] for row in existing_ids])

    new_rows_added = 0

    for index, row in check1.iterrows():
        if index not in existing_ids:
            values = {
                "id": index,
                "price(R$)": row["price(R$)"],
                "condo(R$)": row["condo(R$)"],
                "district": row["district"],
                "address": row["address"],
                "area(m²)": row["area(m²)"],
                "bedroom": row["bedroom"],
                "bathrooms": row["bathrooms"],
                "parkings": row["parkings"],
                "url(image)": row["url(image)"],
                "url(apt)": row["url(apt)"],
                "created_at": date1
            }
            for key, value in values.items():
                if pd.isna(value):
                    values[key] = None

            try:
                res = supabase.table("data_scrap").upsert(values).execute()
                new_rows_added += 1
                print(f"Row {index} inserted successfully")
            except Exception as e:
                supabase.table("entradas").upsert(
                    {"error": str(e), "status": "failed"}).execute()
                print(f"Error inserting row {index}: {e}")

    if new_rows_added > 0:
        print(f"{new_rows_added} rows added to 'data_scrap' table")
        date2 = (datetime.utcnow() - timedelta(hours=3)
                 ).strftime("%Y-%m-%dT%H:%M:%S")
        try:
            # Insert the number of new rows added into the 'entrada' table
            supabase.table("entradas").upsert(
                {"error": None, "prop_scrap": new_rows_added, "created_at": date1, "status": "complete", "completed_at": date2, "pages": url_list}).execute()
        except Exception as e:
            # Insert the error message into the table
            supabase.table("entradas").upsert(
                {"error": str(e), "status": "failed"}).execute()
    else:
        print("There is nothing to add")

    print("Time to look at your csv file and supabase!!!")
