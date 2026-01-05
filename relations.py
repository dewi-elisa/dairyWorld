import pandas as pd
from bs4 import BeautifulSoup
import requests
import ast
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


def get_info(URL, mention):
    # get wikipedia page
    page = SESSION.get(URL)

    # find paragraphs mentioning the other entity
    soup = BeautifulSoup(page.text, 'html.parser')
    info = []
    for paragraph in soup.find_all('p'):
        if mention in paragraph.text:
            info.append(paragraph.text)

    return info


def get_relations(ingredient):
    product, countries, description, productURL, countryURLs = ingredient
    print(f'Extracting information about {product}...')

    # get info from product page
    for country in countries:
        product_info = get_info(productURL, country)

    # get info from country page(s)
    country_info = {}
    for country, countryURL in zip(countries, countryURLs):
        country_info[country] = get_info(countryURL, product)

    return product, countries, description, product_info, country_info


if __name__ == '__main__':
    # get data
    products = pd.read_csv('data/products.csv', converters={
        'countries': ast.literal_eval,
        'countryURLs': ast.literal_eval
    })
    print('Data loaded from data/products.csv!')

    # extract relations
    relations = products.apply(get_relations, axis=1)
    relations.columns = [
        'product',
        'countries',
        'description',
        'CountryMentionInProductURL',
        'productMentionInCountryURLs']

    relations.to_csv('data/relations.csv', sep=',', index=False)
    print('Relations saved to data/relations.csv')
    print('Done!')
