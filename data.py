import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

USER_AGENT = os.getenv('WIKIMEDIA_USER_AGENT')
if not USER_AGENT:
    raise RuntimeError('No USER_AGENT set in environment variables!')

SESSION = requests.Session()
SESSION.headers.update(
    {
        'User-Agent': USER_AGENT,
        'Accept-Language': 'en'
    }
)


def get_website(url, file_name):
    page = SESSION.get(url)
    text = page.text
    with open(file_name, 'w') as file:
        file.write(str(text))


def check_URL(URL):
    if URL[:6] != '/wiki/':
        return None
    return 'https://en.wikipedia.org' + URL


def clean_product(details):
    if details == []:  # if it is a header
        return None

    product, _, country, description = details

    # clean description
    description = description.get_text(' ', strip=True)

    # extract product name and URL
    product = product.find('a')

    if product is None:  # if the product does not have an URL
        print('    Product has no URLs')
        return None

    product_name = product.text
    productURL = check_URL(product['href'])

    if productURL is None:  # if the product has an URL but does not exist
        print(f'    Product {product_name} has no productURL')
        return None

    # extract countries and URLs
    countries = country.find_all('a')

    if countries == []:  # if the product does not have a country
        print(f'    {product_name}\'s country has no URLs')
        return None

    country_name = []
    countryURLs = []
    for country in countries:
        country_name.append(country.text)
        countryURLs.append(check_URL(country['href']))

    if countryURLs == [None]:  # if the country URL does not exist
        print(f'    Product {product_name} has no countryURL')
        return None

    return product_name, country_name, description, productURL, countryURLs


if __name__ == '__main__':
    # get the website if not already scraped
    file_name = 'data/dairy_products.html'

    if not os.path.isfile(file_name):
        print('Extracting the website...')
        URL = 'https://en.wikipedia.org/wiki/List_of_dairy_products'
        get_website(URL, file_name)

    print('Found the website!')

    # extract the tables
    print('Extracting tables...')
    with open(file_name) as file:
        soup = BeautifulSoup(file, 'html.parser')

    # the tables with dairy products have class 'wikitable sortable'
    tables = soup.select('table.wikitable.sortable')

    # save an example of a table
    with open('data/example_table.html', 'w') as file:
        file.write(str(tables[0]))

    # should be 23
    print(f'Found {len(tables)} tables!')

    # create the dataframe
    df = pd.DataFrame(columns=['product', 'countries', 'description', 'productURL', 'countryURLs'])

    print('Created dataframe!')
    print('Adding products...')

    # extract the products and add to dataframe
    removed = 0
    for table in tables:
        for row in table.find_all('tr'):
            # return the product if it is not a header and it has all elements
            if row.find('th') is not None:  # header
                continue

            details = row.find_all('td')
            details = clean_product(details)
            if details is None:
                removed += 1
            else:  # if all columns exist
                product, country, description, productURL, countryURLs = details
                df.loc[len(df)] = [product, country, description, productURL, countryURLs]

    print(f'Removed {removed} products due to incomplete information.')
    print(f'Found {len(df)} products!')

    # add some things manually?

    # save the dataframe
    print('Saving the dataframe...')
    df.to_csv('data/products.csv', sep=',', index=False)

    print('Done!')
