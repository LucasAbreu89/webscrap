def scrap_buy(x, y=None, url_type="normal"):
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
    import googlemaps
    import time
    import os
    from unidecode import unidecode
    from dotenv import load_dotenv
    from rapidfuzz import fuzz
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning)

    load_dotenv()

    url_supa = os.environ.get("SUPABASE_URL")
    key_supa = os.environ.get("SUPABASE_KEY2")
    key_google = os.environ.get("API_GOOGLE")

    supabase = create_client(url_supa, key_supa)
    gmaps = googlemaps.Client(key=key_google)

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

    header = ("price(R$)", "condo(R$)", "district", "address", "area(m²)",
              "bedroom", "bathrooms", "parkings", "url(image)", "url(apt)", "regional", "lat", "lng")

    servico = Service(ChromeDriverManager().install())
    check = pd.DataFrame(columns=header)

    # creating a header for my list

    for page_num in page_range:
        start_time = time.time()
        url = url_template.format(page_num)
        driver = webdriver.Chrome(service=servico, options=option)
        driver.get(url)

        time.sleep(5)
        for i in range(16):
            driver.execute_script("window.scrollBy(0, 550)")
            time.sleep(0.4)

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
        area_list = [x.split('m²')[1].strip() if x.count('m²') > 1 and isinstance(x, str) else
                     (x.split('m²')[0] + 'm²' if 'm²' in x and isinstance(x, str) else np.nan) for x in features1]
        area_list = [x.split()[0].replace('m²', '').strip()
                     if isinstance(x, str) else np.nan for x in area_list]
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

        # cleaning district
        district_list = [unidecode(x) for x in district_list]
        district_list = [x.title() for x in district_list]
        district_list = [re.sub(r'\([^)]*\)', '', x).strip()
                         for x in district_list]
        district_list = [x.replace("ç", "c") for x in district_list]

        # creating Regional
        regional = []

        # Loop over the district_list
        my_dict = {'Alta Tensao': 'Barreiro', 'Aarao Reis': 'Norte', 'Acaba Mundo': 'Centro-sul', 'Acaiaca': 'Nordeste', 'Ademar Maldonado': 'Barreiro', 'Aeroporto': 'Pampulha', 'Aguas Claras': 'Barreiro', 'Alipio De Melo': 'Pampulha', 'Alpes': 'Oeste', 'Alto Barroca': 'Oeste', 'Alto Caicaras': 'Noroeste', 'Alto Das Antenas': 'Barreiro', 'Alto Dos Pinheiros': 'Noroeste', 'Alto Vera Cruz': 'Leste', 'Alvaro Camargos': 'Noroeste', 'Ambrosina': 'Oeste', 'Anchieta': 'Centro-sul', 'Andiroba': 'Nordeste', 'Antonio Ribeiro De Abreu': 'Nordeste', 'Aparecida': 'Noroeste', 'Aparecida Setima Secao': 'Noroeste', 'Apia': 'Centro-sul', 'Apolonia': 'Venda nova', 'Araguaia': 'Barreiro', 'Atila De Paiva': 'Barreiro', 'Bacurau': 'Norte', 'Bairro Das Industrias I': 'Barreiro', 'Bairro Das Industrias II': 'Oeste', 'Bairro Novo Das Industrias': 'Barreiro', 'Baleia': 'Leste', 'Bandeirantes': 'Pampulha', 'Barao Homem De Melo': 'Oeste', 'Barreiro': 'Barreiro', 'Barro Preto': 'Centro-sul', 'Barroca': 'Oeste', 'Beija Flor': 'Nordeste', 'Beira-Linha': 'Nordeste', 'Bela Vitoria': 'Nordeste', 'Belem': 'Leste', 'Belmonte': 'Nordeste', 'Belvedere': 'Centro-sul', 'Bernadete': 'Barreiro', 'Betania': 'Oeste', 'Biquinhas': 'Norte', 'Bispo De Maura': 'Pampulha', 'Boa Esperanca': 'Nordeste', 'Boa Uniao': 'Norte', 'Boa Viagem': 'Centro-sul', 'Boa Vista': 'Leste', 'Bom Jesus': 'Noroeste', 'Bonfim': 'Noroeste', 'Bonsucesso': 'Barreiro', 'Brasil Industrial': 'Barreiro', 'Braunas': 'Pampulha', 'Buritis': 'Oeste', 'Cabana Do Pai Tomas': 'Oeste', 'Cachoeirinha': 'Nordeste', 'Caetano Furquim': 'Leste', 'Caicara-Adelaide': 'Noroeste', 'Caicaras': 'Noroeste', 'Caicara': 'Noroeste', 'Calafate': 'Oeste', 'California': 'Noroeste', 'Camargos': 'Oeste', 'Campo Alegre': 'Norte', 'Camponesa': 'Leste', 'Campus Ufmg': 'Pampulha', 'Canaa': 'Venda nova', 'Canada': 'Nordeste', 'Candelaria': 'Venda nova', 'Capitao Eduardo': 'Nordeste', 'Cardoso': 'Barreiro', 'Carlos Prates': 'Noroeste', 'Carmo': 'Centro-sul', 'Casa Branca': 'Leste', 'Castanheira': 'Barreiro', 'Castelo': 'Pampulha', 'Cdi Jatoba': 'Barreiro', 'Cenaculo': 'Venda nova', 'Centro': 'Centro-sul', 'Ceu Azul': 'Pampulha', 'Chacara Leonina': 'Oeste', 'Cidade Jardim': 'Centro-sul', 'Cidade Jardim Taquaril': 'Leste', 'Cidade Nova': 'Nordeste', 'Cinquentenario': 'Oeste', 'Colegio Batista': 'Nordeste', 'Comiteco': 'Centro-sul', 'Concordia': 'Nordeste', 'Conego Pinheiro': 'Leste', 'Conego Pinheiro A': 'Leste', 'Confisco': 'Pampulha', 'Conjunto Bonsucesso': 'Barreiro', 'Conjunto California': 'Noroeste', 'Conjunto Capitao Eduardo': 'Nordeste', 'Conjunto Celso Machado': 'Pampulha', 'Conjunto Floramar': 'Norte', 'Conjunto Jardim Filadelfia': 'Noroeste', 'Conjunto Jatoba': 'Barreiro', 'Conjunto Lagoa': 'Pampulha', 'Conjunto Minascaixa': 'Venda nova', 'Conjunto Novo Dom Bosco': 'Noroeste', 'Conjunto Paulo': 'Nordeste', 'Conjunto Providencia': 'Norte', 'Conjunto Santa Maria': 'Centro-sul', 'Conjunto Sao Francisco De Assis': 'Pampulha', 'Conjunto Serra Verde': 'Venda nova', 'Conjunto Taquaril': 'Leste', 'Copacabana': 'Pampulha', 'Coqueiros': 'Noroeste', 'Coracao De Jesus': 'Centro-sul', 'Coracao Eucaristico': 'Noroeste', 'Corumbiara': 'Barreiro', 'Cruzeiro': 'Centro-sul', 'Custodinha': 'Oeste', 'Delta': 'Noroeste', 'Diamante': 'Barreiro', 'Distrito Industrial Do Jatoba': 'Barreiro', 'Dom Bosco': 'Noroeste', 'Dom Cabral': 'Noroeste', 'Dom Joaquim': 'Nordeste', 'Dom Silverio': 'Nordeste', 'Dona Clara': 'Pampulha', 'Engenho Nogueira': 'Pampulha', 'Ermelinda': 'Noroeste', 'Ernesto Do Nascimento': 'Barreiro', 'Esperanca': 'Barreiro', 'Esplanada': 'Leste', 'Estoril': 'Oeste', 'Estrela': 'Centro-sul', 'Estrela Do Oriente': 'Oeste', 'Etelvina Carneiro': 'Norte', 'Europa': 'Venda nova', 'Eymard': 'Nordeste', 'Fazendinha': 'Centro-sul', 'Fernao Dias': 'Nordeste', 'Flamengo': 'Venda nova', 'Flavio De Oliveira': 'Barreiro', 'Flavio Marques Lisboa': 'Barreiro', 'Floramar': 'Norte', 'Floresta': 'Centro-sul', 'Frei Leopoldo': 'Norte', 'Funcionarios': 'Centro-sul', 'Gameleira': 'Oeste', 'Garcas': 'Pampulha', 'Gloria': 'Noroeste', 'Goiania': 'Nordeste', 'Graca': 'Nordeste', 'Grajau': 'Oeste', 'Granja De Freitas': 'Leste', 'Granja Werneck': 'Norte', 'Grota': 'Leste', 'Grotinha': 'Nordeste', 'Guanabara': 'Nordeste', 'Guarani': 'Norte', 'Guarata': 'Oeste', 'Gutierrez': 'Oeste', 'Havai': 'Oeste', 'Heliopolis': 'Norte', 'Horto': 'Leste', 'Horto Florestal': 'Leste', 'Imbaubas': 'Oeste', 'Inconfidencia': 'Pampulha', 'Indaia': 'Pampulha', 'Independencia': 'Barreiro', 'Ipe': 'Nordeste', 'Ipiranga': 'Nordeste', 'Itaipu': 'Barreiro', 'Itapoa': 'Pampulha', 'Itatiaia': 'Pampulha', 'Jaqueline': 'Norte', 'Jaragua': 'Pampulha', 'Jardim Alvorada': 'Pampulha', 'Jardim America': 'Oeste', 'Jardim Atlantico': 'Pampulha', 'Jardim Do Vale': 'Barreiro', 'Jardim Dos Comerciarios': 'Venda nova', 'Jardim Felicidade': 'Norte', 'Jardim Guanabara': 'Norte', 'Jardim Leblon': 'Venda nova', 'Jardim Montanhes': 'Noroeste', 'Jardim Sao Jose': 'Pampulha', 'Jardim Vitoria': 'Nordeste', 'Jardinopolis': 'Oeste', 'Jatoba': 'Barreiro', 'Joao Alfredo': 'Leste', 'Joao Paulo Ii': 'Barreiro', 'Joao Pinheiro': 'Noroeste', 'Jonas Veiga': 'Leste', 'Juliana': 'Norte', 'Lagoa': 'Venda nova', 'Lagoa Da Pampulha': 'Pampulha', 'Lagoinha': 'Noroeste', 'Lagoinha Leblon': 'Venda nova', 'Lajedo': 'Norte', 'Laranjeiras': 'Venda nova', 'Leonina': 'Oeste', 'Leticia': 'Venda nova', 'Liberdade': 'Pampulha', 'Lindeia': 'Barreiro', 'Lorena': 'Noroeste', 'Lourdes': 'Centro-sul', 'Luxemburgo': 'Centro-sul', 'Madre Gertrudes': 'Oeste', 'Madri': 'Norte', 'Mala E Cuia': 'Centro-sul', 'Manacas': 'Pampulha', 'Mangabeiras': 'Centro-sul', 'Mangueiras': 'Barreiro', 'Mantiqueira': 'Venda nova', 'Marajo': 'Oeste', 'Maravilha': 'Oeste', 'Marcola': 'Centro-sul', 'Maria Goretti': 'Nordeste', 'Maria Helena': 'Venda nova', 'Maria Teresa': 'Norte', 'Maria Virginia': 'Nordeste', 'Mariano De Abreu': 'Leste', 'Marieta': 'Barreiro', 'Marilandia': 'Barreiro', 'Mariquinhas': 'Norte', 'Marmiteiros': 'Noroeste', 'Milionarios': 'Barreiro', 'Minas Brasil': 'Noroeste', 'Minascaixa': 'Venda nova', 'Minaslandia': 'Norte', 'Mineirao': 'Barreiro', 'Miramar': 'Barreiro', 'Mirante': 'Norte', 'Mirtes': 'Nordeste', 'Monsenhor Messias': 'Noroeste', 'Monte Azul': 'Norte', 'Monte Sao Jose': 'Centro-sul', 'Morro Dos Macacos': 'Nordeste', 'Nazare': 'Nordeste', 'Nossa Senhora Da Aparecida': 'Centro-sul', 'Nossa Senhora Da Conceicao': 'Centro-sul', 'Nossa Senhora De Fatima': 'Centro-sul',
                   'Nossa Senhora Do Rosario': 'Centro-sul', 'Nova America': 'Venda nova', 'Nova Cachoeirinha': 'Noroeste', 'Nova Cintra': 'Oeste', 'Nova Esperanca': 'Noroeste', 'Nova Floresta': 'Nordeste', 'Nova Gameleira': 'Oeste', 'Nova Granada': 'Oeste', 'Nova Pampulha': 'Pampulha', 'Nova Suissa': 'Oeste', 'Nova Vista': 'Leste', 'Novo Aarao Reis': 'Norte', 'Novo Gloria': 'Noroeste', 'Novo Ouro Preto': 'Pampulha', 'Novo Santa Cecilia': 'Barreiro', 'Novo Sao Lucas': 'Centro-sul', 'Novo Tupi': 'Norte', 'Oeste': 'Oeste', 'Olaria': 'Barreiro', "Olhos D'Agua": 'Barreiro', 'Ouro Minas': 'Nordeste', 'Ouro Preto': 'Pampulha', 'Padre Eustaquio': 'Noroeste', 'Palmares': 'Nordeste', 'Palmeiras': 'Oeste', 'Pantanal': 'Oeste', 'Paqueta': 'Pampulha', 'Paraiso': 'Leste', 'Parque Sao Jose': 'Oeste', 'Parque Sao Pedro': 'Venda nova', 'Paulo Vi': 'Nordeste', 'Pedreira Prado Lopes': 'Noroeste', 'Penha': 'Nordeste', 'Petropolis': 'Barreiro', 'Pilar': 'Barreiro', 'Pindorama': 'Noroeste', 'Pindura Saia': 'Centro-sul', 'Piraja': 'Nordeste', 'Piratininga': 'Venda nova', 'Pirineus': 'Leste', 'Planalto': 'Norte', 'Pompeia': 'Leste', 'Pongelupe': 'Barreiro', 'Pousada Santo Antonio': 'Nordeste', 'Prado': 'Oeste', 'Primeiro De Maio': 'Norte', 'Providencia': 'Norte', 'Renascenca': 'Nordeste', 'Ribeiro De Abreu': 'Nordeste', 'Rio Branco': 'Venda nova', 'Sagrada Familia': 'Leste', 'Salgado Filho': 'Oeste', 'Santa Amelia': 'Pampulha', 'Santa Branca': 'Pampulha', 'Santa Cecilia': 'Barreiro', 'Santa Cruz': 'Nordeste', 'Santa Efigenia': 'Leste', 'Santa Helena': 'Barreiro', 'Santa Ines': 'Leste', 'Santa Isabel': 'Centro-sul', 'Santa Lucia': 'Oeste', 'Santa Margarida': 'Barreiro', 'Santa Maria': 'Oeste', 'Santa Monica': 'Pampulha', 'Santa Rita': 'Barreiro', 'Santa Rita De Cassia': 'Centro-sul', 'Santa Rosa': 'Pampulha', 'Santa Sofia': 'Oeste', 'Santa Tereza': 'Leste', 'Santa Terezinha': 'Pampulha', 'Santana Do Cafezal': 'Centro-sul', 'Santo Agostinho': 'Centro-sul', 'Santo Andre': 'Noroeste', 'Santo Antonio': 'Centro-sul', 'Sao Benedito': 'Nordeste', 'Sao Bento': 'Centro-sul', 'Sao Bernardo': 'Norte', 'Sao Cristovao': 'Noroeste', 'Sao Damiao': 'Venda nova', 'Sao Francisco': 'Pampulha', 'Sao Francisco Das Chagas': 'Noroeste', 'Sao Gabriel': 'Nordeste', 'Sao Geraldo': 'Leste', 'Sao Goncalo': 'Norte', 'Sao Joao': 'Barreiro', 'Sao Joao Batista': 'Venda nova', 'Sao Jorge': 'Oeste', 'Sao Jose': 'Pampulha', 'Sao Lucas': 'Centro-sul', 'Sao Luiz': 'Pampulha', 'Sao Marcos': 'Nordeste', 'Sao Paulo': 'Nordeste', 'Sao Pedro': 'Centro-sul', 'Sao Salvador': 'Noroeste', 'Sao Sebastiao': 'Nordeste', 'Sao Tomaz': 'Norte', 'Sao Vicente': 'Leste', 'Satelite': 'Norte', 'Saudade': 'Leste', 'Savassi': 'Centro-sul', 'Senhor Dos Passos': 'Noroeste', 'Serra': 'Centro-sul', 'Serra Do Curral': 'Barreiro', 'Serra Verde': 'Venda nova', 'Serrano': 'Pampulha', 'Silveira': 'Nordeste', 'Sion': 'Centro-sul', 'Solar Do Barreiro': 'Barreiro', 'Solimoes': 'Norte', 'Sport Club': 'Oeste', 'Sumare': 'Noroeste', 'Suzana': 'Pampulha', 'Taquaril': 'Leste', 'Teixeira Dias': 'Barreiro', 'Tiradentes': 'Nordeste', 'Tirol': 'Barreiro', 'Tres Marias': 'Nordeste', 'Trevo': 'Pampulha', 'Tunel De Ibirite': 'Barreiro', 'Tupi A': 'Norte', 'Tupi B': 'Norte', 'Uniao': 'Nordeste', 'Unidas': 'Venda nova', 'Universitario': 'Pampulha', 'Universo': 'Venda nova', 'Urca': 'Pampulha', 'Vale Do Jatoba': 'Barreiro', 'Varzea Da Palma': 'Venda nova', 'Venda Nova': 'Venda nova', 'Ventosa': 'Oeste', 'Vera Cruz': 'Leste', 'Vila Aeroporto': 'Norte', 'Vila Aeroporto Jaragua': 'Pampulha', 'Vila Antena': 'Oeste', 'Vila Antena Montanhes': 'Pampulha', 'Vila Atila De Paiva': 'Barreiro', 'Vila Bandeirantes': 'Centro-sul', 'Vila Barragem Santa Lucia': 'Centro-sul', 'Vila Batik': 'Barreiro', 'Vila Betania': 'Oeste', 'Vila Boa Vista': 'Leste', 'Vila Calafate': 'Oeste', 'Vila California': 'Noroeste', 'Vila Canto Do Sabia': 'Venda nova', 'Vila Cemig': 'Barreiro', 'Vila Cloris': 'Norte', 'Vila Copacabana': 'Venda nova', 'Vila Copasa': 'Barreiro', 'Vila Coqueiral': 'Noroeste', 'Vila Da Amizade': 'Oeste', 'Vila Da Area': 'Leste', 'Vila Da Luz': 'Nordeste', 'Vila Da Paz': 'Nordeste', 'Vila Das Oliveiras': 'Noroeste', 'Vila De Sa': 'Nordeste', 'Vila Dias': 'Leste', 'Vila Do Pombal': 'Nordeste', 'Vila Dos Anjos': 'Venda nova', 'Vila Ecologica': 'Barreiro', 'Vila Engenho Nogueira': 'Pampulha', 'Vila Esplanada': 'Nordeste', 'Vila Formosa': 'Barreiro', 'Vila Fumec': 'Centro-sul', 'Vila Havai': 'Oeste', 'Vila Independencia': 'Barreiro', 'Vila Inestan': 'Nordeste', 'Vila Ipiranga': 'Nordeste', 'Vila Jardim Alvorada': 'Pampulha', 'Vila Jardim Leblon': 'Venda nova', 'Vila Jardim Montanhes': 'Pampulha', 'Vila Jardim Sao Jose': 'Pampulha', 'Vila Madre Gertrudes': 'Oeste', 'Vila Maloca': 'Noroeste', 'Vila Mangueiras': 'Barreiro', 'Vila Mantiqueira': 'Venda nova', 'Vila Maria': 'Nordeste', 'Vila Minaslandia': 'Norte', 'Vila Nossa Senhora Aparecida': 'Venda nova', 'Vila Nossa Senhora Do Rosario': 'Leste', 'Vila Nova': 'Norte', 'Vila Nova Cachoeirinha': 'Noroeste', 'Vila Nova Dos Milionarios': 'Barreiro', 'Vila Nova Gameleira': 'Oeste', 'Vila Nova Paraiso': 'Oeste', 'Vila Novo Sao Lucas': 'Centro-sul', 'Vila Oeste': 'Oeste', "Vila Olhos D'Agua": 'Barreiro', 'Vila Ouro Minas': 'Nordeste', 'Vila Paqueta': 'Pampulha', 'Vila Paraiso': 'Leste', 'Vila Paris': 'Centro-sul', 'Vila Petropolis': 'Barreiro', 'Vila Pilar': 'Barreiro', 'Vila Pinho': 'Barreiro', 'Vila Piratininga': 'Barreiro', 'Vila Piratininga Venda Nova': 'Venda nova', 'Vila Primeiro De Maio': 'Norte', 'Vila Puc': 'Noroeste', 'Vila Real': 'Pampulha', 'Vila Rica': 'Pampulha', 'Vila Santa Monica': 'Venda nova', 'Vila Santa Rosa': 'Pampulha', 'Vila Santo Antonio': 'Pampulha', 'Vila Santo Antonio Barroquinha': 'Pampulha', 'Vila Sao Dimas': 'Nordeste', 'Vila Sao Francisco': 'Pampulha', 'Vila Sao Gabriel': 'Nordeste', 'Vila Sao Gabriel Jacui': 'Nordeste', 'Vila Sao Geraldo': 'Leste', 'Vila Sao Joao Batista': 'Venda nova', 'Vila Sao Paulo': 'Nordeste', 'Vila Sao Rafael': 'Leste', 'Vila Satelite': 'Venda nova', 'Vila Sesc': 'Venda nova', 'Vila Sumare': 'Noroeste', 'Vila Suzana': 'Pampulha', 'Vila Tirol': 'Barreiro', 'Vila Trinta E Um De Marco': 'Noroeste', 'Vila Uniao': 'Leste', 'Vila Vera Cruz': 'Leste', 'Vila Vista Alegre': 'Oeste', 'Virginia': 'Oeste', 'Vista Alegre': 'Oeste', 'Vista Do Sol': 'Nordeste', 'Vitoria': 'Nordeste', 'Vitoria Da Conquista': 'Barreiro', 'Xangri-La': 'Pampulha', 'Xodo-Marize': 'Norte', 'Zilah Sposito': 'Norte'}

        for district in district_list:
            # Check if the district is in my_dict
            if district in my_dict:
                regional.append(my_dict[district])
            else:
                # find the closest match to the district in my_dict
                ratios = [(fuzz.ratio(district, key), key)
                          for key in my_dict.keys()]
                closest_match = max(ratios, key=lambda x: x[0])[1]
                # add the value for the closest match to the regional list
                regional.append(my_dict[closest_match])

        endereco_list = [str(address) + ", " + str(district) +
                         ", Belo Horizonte" for address, district in zip(address_list, district_list)]

        lat = []
        lng = []
        geocode_result = gmaps.geocode(endereco_list)

        for endereco in endereco_list:
            geocode_result = gmaps.geocode(endereco)
            if not geocode_result:
                lat.append(np.nan)
                lng.append(np.nan)
            else:
                location = geocode_result[0]['geometry']['location']
                lat.append(location['lat'])
                lng.append(location['lng'])

        # creating a list of tuples
        total = list(zip(prices_brl, condos_brl, district_list, address_list, area_list,
                     bedrooms_list, baths_list, parking_list, src_list, full_links, regional, lat, lng))

        unique_total = []
        # iterate over each tuple in the total list
        for row in total:
            # check if the row is already in the unique_total list
            if row not in unique_total:
                # if not, append the row to the unique_total list
                unique_total.append(row)

        check = check.append(pd.DataFrame(unique_total, columns=header))

        # check.drop_duplicates(inplace=True)
        check["price(R$)"] = check["price(R$)"].astype(float)
        check["area(m²)"] = check["area(m²)"].astype(float)
        check['parkings'] = check['parkings'].astype('Int64')

        end_time = time.time()
        diference_time = end_time - start_time

        print(f"page {page_num} was scraped in {round(diference_time)} seconds")

        total_shape = check.shape
        unique_check = check.drop_duplicates()
        unique_shape = unique_check.shape
        print("Total shape of check DataFrame: ", total_shape)
        print("Shape of unique rows in check DataFrame: ", unique_shape)
        driver.quit()

    # Get existing IDs in the table
    existing_ids = supabase.table("data_scrap").select("id").execute().data

    # Convert the IDs to a set for efficient membership testing
    existing_ids = set([row["id"] for row in existing_ids])

    # Get the last used ID in the table
    last_id = max(existing_ids) if existing_ids else 0

    new_rows_added = 0

    for index, row in check.iterrows():
        # Increment the ID for each new row
        last_id += 1

        if last_id not in existing_ids:
            values = {
                "id": last_id,
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
                "created_at": date1,
                "regional": row["regional"],
                "lat": row["lat"],
                "lng": row["lng"]
            }
            for key, value in values.items():
                if pd.isna(value):
                    values[key] = None

            try:
                res = supabase.table("data_scrap").upsert(values).execute()
                new_rows_added += 1
                print(f"Row {last_id} inserted successfully")
            except Exception as e:
                supabase.table("entradas").upsert(
                    {"error": str(e), "status": "failed"}).execute()
                print(f"Error inserting row {last_id}: {e}")

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


def scrap_rent(x, y=None, url_type="normal"):
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
    import googlemaps
    import time
    import os
    from unidecode import unidecode
    from dotenv import load_dotenv
    from rapidfuzz import fuzz
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning)

    load_dotenv()

    url_supa = os.environ.get("SUPABASE_URL")
    key_supa = os.environ.get("SUPABASE_KEY2")
    key_google = os.environ.get("API_GOOGLE")

    supabase = create_client(url_supa, key_supa)
    gmaps = googlemaps.Client(key=key_google)

    if x == 0:
        raise ValueError("The value of x cannot be zero.")

    if y is None:
        # Single page input
        page_range = [x]
    else:
        # Multiple pages input
        page_range = range(x, y)

    if url_type == "normal":
        url_template = "https://www.imovelweb.com.br/apartamentos-aluguel-belo-horizonte-mg-pagina-{}.html"
    elif url_type == "last-day":
        url_template = "https://www.imovelweb.com.br/apartamentos-aluguel-belo-horizonte-mg-publicado-no-ultimo-dia-pagina-{}.html"
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

    header = ("price(R$)", "condo(R$)", "district", "address", "area(m²)",
              "bedroom", "bathrooms", "parkings", "url(image)", "url(apt)", "regional", "lat", "lng")

    servico = Service(ChromeDriverManager().install())
    check = pd.DataFrame(columns=header)

    # creating a header for my list

    for page_num in page_range:
        start_time = time.time()
        url = url_template.format(page_num)
        driver = webdriver.Chrome(service=servico, options=option)
        driver.get(url)

        time.sleep(5)
        for i in range(16):
            driver.execute_script("window.scrollBy(0, 550)")
            time.sleep(0.4)

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
        area_list = [x.split('m²')[1].strip() if x.count('m²') > 1 and isinstance(x, str) else
                     (x.split('m²')[0] + 'm²' if 'm²' in x and isinstance(x, str) else np.nan) for x in features1]
        area_list = [x.split()[0].replace('m²', '').strip()
                     if isinstance(x, str) else np.nan for x in area_list]
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

        # cleaning district
        district_list = [unidecode(x) for x in district_list]
        district_list = [x.title() for x in district_list]
        district_list = [re.sub(r'\([^)]*\)', '', x).strip()
                         for x in district_list]
        district_list = [x.replace("ç", "c") for x in district_list]

        # creating Regional
        regional = []

        # Loop over the district_list
        my_dict = {'Alta Tensao': 'Barreiro', 'Aarao Reis': 'Norte', 'Acaba Mundo': 'Centro-sul', 'Acaiaca': 'Nordeste', 'Ademar Maldonado': 'Barreiro', 'Aeroporto': 'Pampulha', 'Aguas Claras': 'Barreiro', 'Alipio De Melo': 'Pampulha', 'Alpes': 'Oeste', 'Alto Barroca': 'Oeste', 'Alto Caicaras': 'Noroeste', 'Alto Das Antenas': 'Barreiro', 'Alto Dos Pinheiros': 'Noroeste', 'Alto Vera Cruz': 'Leste', 'Alvaro Camargos': 'Noroeste', 'Ambrosina': 'Oeste', 'Anchieta': 'Centro-sul', 'Andiroba': 'Nordeste', 'Antonio Ribeiro De Abreu': 'Nordeste', 'Aparecida': 'Noroeste', 'Aparecida Setima Secao': 'Noroeste', 'Apia': 'Centro-sul', 'Apolonia': 'Venda nova', 'Araguaia': 'Barreiro', 'Atila De Paiva': 'Barreiro', 'Bacurau': 'Norte', 'Bairro Das Industrias I': 'Barreiro', 'Bairro Das Industrias II': 'Oeste', 'Bairro Novo Das Industrias': 'Barreiro', 'Baleia': 'Leste', 'Bandeirantes': 'Pampulha', 'Barao Homem De Melo': 'Oeste', 'Barreiro': 'Barreiro', 'Barro Preto': 'Centro-sul', 'Barroca': 'Oeste', 'Beija Flor': 'Nordeste', 'Beira-Linha': 'Nordeste', 'Bela Vitoria': 'Nordeste', 'Belem': 'Leste', 'Belmonte': 'Nordeste', 'Belvedere': 'Centro-sul', 'Bernadete': 'Barreiro', 'Betania': 'Oeste', 'Biquinhas': 'Norte', 'Bispo De Maura': 'Pampulha', 'Boa Esperanca': 'Nordeste', 'Boa Uniao': 'Norte', 'Boa Viagem': 'Centro-sul', 'Boa Vista': 'Leste', 'Bom Jesus': 'Noroeste', 'Bonfim': 'Noroeste', 'Bonsucesso': 'Barreiro', 'Brasil Industrial': 'Barreiro', 'Braunas': 'Pampulha', 'Buritis': 'Oeste', 'Cabana Do Pai Tomas': 'Oeste', 'Cachoeirinha': 'Nordeste', 'Caetano Furquim': 'Leste', 'Caicara-Adelaide': 'Noroeste', 'Caicaras': 'Noroeste', 'Caicara': 'Noroeste', 'Calafate': 'Oeste', 'California': 'Noroeste', 'Camargos': 'Oeste', 'Campo Alegre': 'Norte', 'Camponesa': 'Leste', 'Campus Ufmg': 'Pampulha', 'Canaa': 'Venda nova', 'Canada': 'Nordeste', 'Candelaria': 'Venda nova', 'Capitao Eduardo': 'Nordeste', 'Cardoso': 'Barreiro', 'Carlos Prates': 'Noroeste', 'Carmo': 'Centro-sul', 'Casa Branca': 'Leste', 'Castanheira': 'Barreiro', 'Castelo': 'Pampulha', 'Cdi Jatoba': 'Barreiro', 'Cenaculo': 'Venda nova', 'Centro': 'Centro-sul', 'Ceu Azul': 'Pampulha', 'Chacara Leonina': 'Oeste', 'Cidade Jardim': 'Centro-sul', 'Cidade Jardim Taquaril': 'Leste', 'Cidade Nova': 'Nordeste', 'Cinquentenario': 'Oeste', 'Colegio Batista': 'Nordeste', 'Comiteco': 'Centro-sul', 'Concordia': 'Nordeste', 'Conego Pinheiro': 'Leste', 'Conego Pinheiro A': 'Leste', 'Confisco': 'Pampulha', 'Conjunto Bonsucesso': 'Barreiro', 'Conjunto California': 'Noroeste', 'Conjunto Capitao Eduardo': 'Nordeste', 'Conjunto Celso Machado': 'Pampulha', 'Conjunto Floramar': 'Norte', 'Conjunto Jardim Filadelfia': 'Noroeste', 'Conjunto Jatoba': 'Barreiro', 'Conjunto Lagoa': 'Pampulha', 'Conjunto Minascaixa': 'Venda nova', 'Conjunto Novo Dom Bosco': 'Noroeste', 'Conjunto Paulo': 'Nordeste', 'Conjunto Providencia': 'Norte', 'Conjunto Santa Maria': 'Centro-sul', 'Conjunto Sao Francisco De Assis': 'Pampulha', 'Conjunto Serra Verde': 'Venda nova', 'Conjunto Taquaril': 'Leste', 'Copacabana': 'Pampulha', 'Coqueiros': 'Noroeste', 'Coracao De Jesus': 'Centro-sul', 'Coracao Eucaristico': 'Noroeste', 'Corumbiara': 'Barreiro', 'Cruzeiro': 'Centro-sul', 'Custodinha': 'Oeste', 'Delta': 'Noroeste', 'Diamante': 'Barreiro', 'Distrito Industrial Do Jatoba': 'Barreiro', 'Dom Bosco': 'Noroeste', 'Dom Cabral': 'Noroeste', 'Dom Joaquim': 'Nordeste', 'Dom Silverio': 'Nordeste', 'Dona Clara': 'Pampulha', 'Engenho Nogueira': 'Pampulha', 'Ermelinda': 'Noroeste', 'Ernesto Do Nascimento': 'Barreiro', 'Esperanca': 'Barreiro', 'Esplanada': 'Leste', 'Estoril': 'Oeste', 'Estrela': 'Centro-sul', 'Estrela Do Oriente': 'Oeste', 'Etelvina Carneiro': 'Norte', 'Europa': 'Venda nova', 'Eymard': 'Nordeste', 'Fazendinha': 'Centro-sul', 'Fernao Dias': 'Nordeste', 'Flamengo': 'Venda nova', 'Flavio De Oliveira': 'Barreiro', 'Flavio Marques Lisboa': 'Barreiro', 'Floramar': 'Norte', 'Floresta': 'Centro-sul', 'Frei Leopoldo': 'Norte', 'Funcionarios': 'Centro-sul', 'Gameleira': 'Oeste', 'Garcas': 'Pampulha', 'Gloria': 'Noroeste', 'Goiania': 'Nordeste', 'Graca': 'Nordeste', 'Grajau': 'Oeste', 'Granja De Freitas': 'Leste', 'Granja Werneck': 'Norte', 'Grota': 'Leste', 'Grotinha': 'Nordeste', 'Guanabara': 'Nordeste', 'Guarani': 'Norte', 'Guarata': 'Oeste', 'Gutierrez': 'Oeste', 'Havai': 'Oeste', 'Heliopolis': 'Norte', 'Horto': 'Leste', 'Horto Florestal': 'Leste', 'Imbaubas': 'Oeste', 'Inconfidencia': 'Pampulha', 'Indaia': 'Pampulha', 'Independencia': 'Barreiro', 'Ipe': 'Nordeste', 'Ipiranga': 'Nordeste', 'Itaipu': 'Barreiro', 'Itapoa': 'Pampulha', 'Itatiaia': 'Pampulha', 'Jaqueline': 'Norte', 'Jaragua': 'Pampulha', 'Jardim Alvorada': 'Pampulha', 'Jardim America': 'Oeste', 'Jardim Atlantico': 'Pampulha', 'Jardim Do Vale': 'Barreiro', 'Jardim Dos Comerciarios': 'Venda nova', 'Jardim Felicidade': 'Norte', 'Jardim Guanabara': 'Norte', 'Jardim Leblon': 'Venda nova', 'Jardim Montanhes': 'Noroeste', 'Jardim Sao Jose': 'Pampulha', 'Jardim Vitoria': 'Nordeste', 'Jardinopolis': 'Oeste', 'Jatoba': 'Barreiro', 'Joao Alfredo': 'Leste', 'Joao Paulo Ii': 'Barreiro', 'Joao Pinheiro': 'Noroeste', 'Jonas Veiga': 'Leste', 'Juliana': 'Norte', 'Lagoa': 'Venda nova', 'Lagoa Da Pampulha': 'Pampulha', 'Lagoinha': 'Noroeste', 'Lagoinha Leblon': 'Venda nova', 'Lajedo': 'Norte', 'Laranjeiras': 'Venda nova', 'Leonina': 'Oeste', 'Leticia': 'Venda nova', 'Liberdade': 'Pampulha', 'Lindeia': 'Barreiro', 'Lorena': 'Noroeste', 'Lourdes': 'Centro-sul', 'Luxemburgo': 'Centro-sul', 'Madre Gertrudes': 'Oeste', 'Madri': 'Norte', 'Mala E Cuia': 'Centro-sul', 'Manacas': 'Pampulha', 'Mangabeiras': 'Centro-sul', 'Mangueiras': 'Barreiro', 'Mantiqueira': 'Venda nova', 'Marajo': 'Oeste', 'Maravilha': 'Oeste', 'Marcola': 'Centro-sul', 'Maria Goretti': 'Nordeste', 'Maria Helena': 'Venda nova', 'Maria Teresa': 'Norte', 'Maria Virginia': 'Nordeste', 'Mariano De Abreu': 'Leste', 'Marieta': 'Barreiro', 'Marilandia': 'Barreiro', 'Mariquinhas': 'Norte', 'Marmiteiros': 'Noroeste', 'Milionarios': 'Barreiro', 'Minas Brasil': 'Noroeste', 'Minascaixa': 'Venda nova', 'Minaslandia': 'Norte', 'Mineirao': 'Barreiro', 'Miramar': 'Barreiro', 'Mirante': 'Norte', 'Mirtes': 'Nordeste', 'Monsenhor Messias': 'Noroeste', 'Monte Azul': 'Norte', 'Monte Sao Jose': 'Centro-sul', 'Morro Dos Macacos': 'Nordeste', 'Nazare': 'Nordeste', 'Nossa Senhora Da Aparecida': 'Centro-sul', 'Nossa Senhora Da Conceicao': 'Centro-sul', 'Nossa Senhora De Fatima': 'Centro-sul',
                   'Nossa Senhora Do Rosario': 'Centro-sul', 'Nova America': 'Venda nova', 'Nova Cachoeirinha': 'Noroeste', 'Nova Cintra': 'Oeste', 'Nova Esperanca': 'Noroeste', 'Nova Floresta': 'Nordeste', 'Nova Gameleira': 'Oeste', 'Nova Granada': 'Oeste', 'Nova Pampulha': 'Pampulha', 'Nova Suissa': 'Oeste', 'Nova Vista': 'Leste', 'Novo Aarao Reis': 'Norte', 'Novo Gloria': 'Noroeste', 'Novo Ouro Preto': 'Pampulha', 'Novo Santa Cecilia': 'Barreiro', 'Novo Sao Lucas': 'Centro-sul', 'Novo Tupi': 'Norte', 'Oeste': 'Oeste', 'Olaria': 'Barreiro', "Olhos D'Agua": 'Barreiro', 'Ouro Minas': 'Nordeste', 'Ouro Preto': 'Pampulha', 'Padre Eustaquio': 'Noroeste', 'Palmares': 'Nordeste', 'Palmeiras': 'Oeste', 'Pantanal': 'Oeste', 'Paqueta': 'Pampulha', 'Paraiso': 'Leste', 'Parque Sao Jose': 'Oeste', 'Parque Sao Pedro': 'Venda nova', 'Paulo Vi': 'Nordeste', 'Pedreira Prado Lopes': 'Noroeste', 'Penha': 'Nordeste', 'Petropolis': 'Barreiro', 'Pilar': 'Barreiro', 'Pindorama': 'Noroeste', 'Pindura Saia': 'Centro-sul', 'Piraja': 'Nordeste', 'Piratininga': 'Venda nova', 'Pirineus': 'Leste', 'Planalto': 'Norte', 'Pompeia': 'Leste', 'Pongelupe': 'Barreiro', 'Pousada Santo Antonio': 'Nordeste', 'Prado': 'Oeste', 'Primeiro De Maio': 'Norte', 'Providencia': 'Norte', 'Renascenca': 'Nordeste', 'Ribeiro De Abreu': 'Nordeste', 'Rio Branco': 'Venda nova', 'Sagrada Familia': 'Leste', 'Salgado Filho': 'Oeste', 'Santa Amelia': 'Pampulha', 'Santa Branca': 'Pampulha', 'Santa Cecilia': 'Barreiro', 'Santa Cruz': 'Nordeste', 'Santa Efigenia': 'Leste', 'Santa Helena': 'Barreiro', 'Santa Ines': 'Leste', 'Santa Isabel': 'Centro-sul', 'Santa Lucia': 'Oeste', 'Santa Margarida': 'Barreiro', 'Santa Maria': 'Oeste', 'Santa Monica': 'Pampulha', 'Santa Rita': 'Barreiro', 'Santa Rita De Cassia': 'Centro-sul', 'Santa Rosa': 'Pampulha', 'Santa Sofia': 'Oeste', 'Santa Tereza': 'Leste', 'Santa Terezinha': 'Pampulha', 'Santana Do Cafezal': 'Centro-sul', 'Santo Agostinho': 'Centro-sul', 'Santo Andre': 'Noroeste', 'Santo Antonio': 'Centro-sul', 'Sao Benedito': 'Nordeste', 'Sao Bento': 'Centro-sul', 'Sao Bernardo': 'Norte', 'Sao Cristovao': 'Noroeste', 'Sao Damiao': 'Venda nova', 'Sao Francisco': 'Pampulha', 'Sao Francisco Das Chagas': 'Noroeste', 'Sao Gabriel': 'Nordeste', 'Sao Geraldo': 'Leste', 'Sao Goncalo': 'Norte', 'Sao Joao': 'Barreiro', 'Sao Joao Batista': 'Venda nova', 'Sao Jorge': 'Oeste', 'Sao Jose': 'Pampulha', 'Sao Lucas': 'Centro-sul', 'Sao Luiz': 'Pampulha', 'Sao Marcos': 'Nordeste', 'Sao Paulo': 'Nordeste', 'Sao Pedro': 'Centro-sul', 'Sao Salvador': 'Noroeste', 'Sao Sebastiao': 'Nordeste', 'Sao Tomaz': 'Norte', 'Sao Vicente': 'Leste', 'Satelite': 'Norte', 'Saudade': 'Leste', 'Savassi': 'Centro-sul', 'Senhor Dos Passos': 'Noroeste', 'Serra': 'Centro-sul', 'Serra Do Curral': 'Barreiro', 'Serra Verde': 'Venda nova', 'Serrano': 'Pampulha', 'Silveira': 'Nordeste', 'Sion': 'Centro-sul', 'Solar Do Barreiro': 'Barreiro', 'Solimoes': 'Norte', 'Sport Club': 'Oeste', 'Sumare': 'Noroeste', 'Suzana': 'Pampulha', 'Taquaril': 'Leste', 'Teixeira Dias': 'Barreiro', 'Tiradentes': 'Nordeste', 'Tirol': 'Barreiro', 'Tres Marias': 'Nordeste', 'Trevo': 'Pampulha', 'Tunel De Ibirite': 'Barreiro', 'Tupi A': 'Norte', 'Tupi B': 'Norte', 'Uniao': 'Nordeste', 'Unidas': 'Venda nova', 'Universitario': 'Pampulha', 'Universo': 'Venda nova', 'Urca': 'Pampulha', 'Vale Do Jatoba': 'Barreiro', 'Varzea Da Palma': 'Venda nova', 'Venda Nova': 'Venda nova', 'Ventosa': 'Oeste', 'Vera Cruz': 'Leste', 'Vila Aeroporto': 'Norte', 'Vila Aeroporto Jaragua': 'Pampulha', 'Vila Antena': 'Oeste', 'Vila Antena Montanhes': 'Pampulha', 'Vila Atila De Paiva': 'Barreiro', 'Vila Bandeirantes': 'Centro-sul', 'Vila Barragem Santa Lucia': 'Centro-sul', 'Vila Batik': 'Barreiro', 'Vila Betania': 'Oeste', 'Vila Boa Vista': 'Leste', 'Vila Calafate': 'Oeste', 'Vila California': 'Noroeste', 'Vila Canto Do Sabia': 'Venda nova', 'Vila Cemig': 'Barreiro', 'Vila Cloris': 'Norte', 'Vila Copacabana': 'Venda nova', 'Vila Copasa': 'Barreiro', 'Vila Coqueiral': 'Noroeste', 'Vila Da Amizade': 'Oeste', 'Vila Da Area': 'Leste', 'Vila Da Luz': 'Nordeste', 'Vila Da Paz': 'Nordeste', 'Vila Das Oliveiras': 'Noroeste', 'Vila De Sa': 'Nordeste', 'Vila Dias': 'Leste', 'Vila Do Pombal': 'Nordeste', 'Vila Dos Anjos': 'Venda nova', 'Vila Ecologica': 'Barreiro', 'Vila Engenho Nogueira': 'Pampulha', 'Vila Esplanada': 'Nordeste', 'Vila Formosa': 'Barreiro', 'Vila Fumec': 'Centro-sul', 'Vila Havai': 'Oeste', 'Vila Independencia': 'Barreiro', 'Vila Inestan': 'Nordeste', 'Vila Ipiranga': 'Nordeste', 'Vila Jardim Alvorada': 'Pampulha', 'Vila Jardim Leblon': 'Venda nova', 'Vila Jardim Montanhes': 'Pampulha', 'Vila Jardim Sao Jose': 'Pampulha', 'Vila Madre Gertrudes': 'Oeste', 'Vila Maloca': 'Noroeste', 'Vila Mangueiras': 'Barreiro', 'Vila Mantiqueira': 'Venda nova', 'Vila Maria': 'Nordeste', 'Vila Minaslandia': 'Norte', 'Vila Nossa Senhora Aparecida': 'Venda nova', 'Vila Nossa Senhora Do Rosario': 'Leste', 'Vila Nova': 'Norte', 'Vila Nova Cachoeirinha': 'Noroeste', 'Vila Nova Dos Milionarios': 'Barreiro', 'Vila Nova Gameleira': 'Oeste', 'Vila Nova Paraiso': 'Oeste', 'Vila Novo Sao Lucas': 'Centro-sul', 'Vila Oeste': 'Oeste', "Vila Olhos D'Agua": 'Barreiro', 'Vila Ouro Minas': 'Nordeste', 'Vila Paqueta': 'Pampulha', 'Vila Paraiso': 'Leste', 'Vila Paris': 'Centro-sul', 'Vila Petropolis': 'Barreiro', 'Vila Pilar': 'Barreiro', 'Vila Pinho': 'Barreiro', 'Vila Piratininga': 'Barreiro', 'Vila Piratininga Venda Nova': 'Venda nova', 'Vila Primeiro De Maio': 'Norte', 'Vila Puc': 'Noroeste', 'Vila Real': 'Pampulha', 'Vila Rica': 'Pampulha', 'Vila Santa Monica': 'Venda nova', 'Vila Santa Rosa': 'Pampulha', 'Vila Santo Antonio': 'Pampulha', 'Vila Santo Antonio Barroquinha': 'Pampulha', 'Vila Sao Dimas': 'Nordeste', 'Vila Sao Francisco': 'Pampulha', 'Vila Sao Gabriel': 'Nordeste', 'Vila Sao Gabriel Jacui': 'Nordeste', 'Vila Sao Geraldo': 'Leste', 'Vila Sao Joao Batista': 'Venda nova', 'Vila Sao Paulo': 'Nordeste', 'Vila Sao Rafael': 'Leste', 'Vila Satelite': 'Venda nova', 'Vila Sesc': 'Venda nova', 'Vila Sumare': 'Noroeste', 'Vila Suzana': 'Pampulha', 'Vila Tirol': 'Barreiro', 'Vila Trinta E Um De Marco': 'Noroeste', 'Vila Uniao': 'Leste', 'Vila Vera Cruz': 'Leste', 'Vila Vista Alegre': 'Oeste', 'Virginia': 'Oeste', 'Vista Alegre': 'Oeste', 'Vista Do Sol': 'Nordeste', 'Vitoria': 'Nordeste', 'Vitoria Da Conquista': 'Barreiro', 'Xangri-La': 'Pampulha', 'Xodo-Marize': 'Norte', 'Zilah Sposito': 'Norte'}

        for district in district_list:
            # Check if the district is in my_dict
            if district in my_dict:
                regional.append(my_dict[district])
            else:
                # find the closest match to the district in my_dict
                ratios = [(fuzz.ratio(district, key), key)
                          for key in my_dict.keys()]
                closest_match = max(ratios, key=lambda x: x[0])[1]
                # add the value for the closest match to the regional list
                regional.append(my_dict[closest_match])

        endereco_list = [str(address) + ", " + str(district) +
                         ", Belo Horizonte" for address, district in zip(address_list, district_list)]

        lat = []
        lng = []
        geocode_result = gmaps.geocode(endereco_list)

        for endereco in endereco_list:
            geocode_result = gmaps.geocode(endereco)
            if not geocode_result:
                lat.append(np.nan)
                lng.append(np.nan)
            else:
                location = geocode_result[0]['geometry']['location']
                lat.append(location['lat'])
                lng.append(location['lng'])

        # creating a list of tuples
        total = list(zip(prices_brl, condos_brl, district_list, address_list, area_list,
                     bedrooms_list, baths_list, parking_list, src_list, full_links, regional, lat, lng))

        unique_total = []
        # iterate over each tuple in the total list
        for row in total:
            # check if the row is already in the unique_total list
            if row not in unique_total:
                # if not, append the row to the unique_total list
                unique_total.append(row)

        check = check.append(pd.DataFrame(unique_total, columns=header))

        # check.drop_duplicates(inplace=True)
        check["price(R$)"] = check["price(R$)"].astype(float)
        check["area(m²)"] = check["area(m²)"].astype(float)
        check['parkings'] = check['parkings'].astype('Int64')

        end_time = time.time()
        diference_time = end_time - start_time

        print(f"page {page_num} was scraped in {round(diference_time)} seconds")

        total_shape = check.shape
        unique_check = check.drop_duplicates()
        unique_shape = unique_check.shape
        print("Total shape of check DataFrame: ", total_shape)
        print("Shape of unique rows in check DataFrame: ", unique_shape)
        driver.quit()

    # Get existing IDs in the table
    existing_ids = supabase.table("rent_scrap").select("id").execute().data

    # Convert the IDs to a set for efficient membership testing
    existing_ids = set([row["id"] for row in existing_ids])

    # Get the last used ID in the table
    last_id = max(existing_ids) if existing_ids else 0

    new_rows_added = 0

    for index, row in check.iterrows():
        # Increment the ID for each new row
        last_id += 1

        if last_id not in existing_ids:
            values = {
                "id": last_id,
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
                "created_at": date1,
                "regional": row["regional"],
                "lat": row["lat"],
                "lng": row["lng"]
            }
            for key, value in values.items():
                if pd.isna(value):
                    values[key] = None

            try:
                res = supabase.table("rent_scrap").upsert(values).execute()
                new_rows_added += 1
                print(f"Row {last_id} inserted successfully")
            except Exception as e:
                supabase.table("rent_entradas").upsert(
                    {"error": str(e), "status": "failed"}).execute()
                print(f"Error inserting row {last_id}: {e}")

    if new_rows_added > 0:
        print(f"{new_rows_added} rows added to 'rent_scrap' table")
        date2 = (datetime.utcnow() - timedelta(hours=3)
                 ).strftime("%Y-%m-%dT%H:%M:%S")
        try:
            # Insert the number of new rows added into the 'entrada' table
            supabase.table("rent_entradas").upsert(
                {"error": None, "prop_scrap": new_rows_added, "created_at": date1, "status": "complete", "completed_at": date2, "pages": url_list}).execute()
        except Exception as e:
            # Insert the error message into the table
            supabase.table("rent_entradas").upsert(
                {"error": str(e), "status": "failed"}).execute()
    else:
        print("There is nothing to add")

    print("Time to look at your csv file and supabase!!!")
