import pandas as pd
from bs4 import BeautifulSoup
import requests
import ast
import os
import re
from dotenv import load_dotenv
load_dotenv()

USER_AGENT = os.getenv("WIKIMEDIA_USER_AGENT")
if not USER_AGENT:
    raise RuntimeError('No USER_AGENT set in environment variables!')

SESSION = requests.Session()
SESSION.headers.update(
    {
        'User-Agent': USER_AGENT,
        "Accept-Language": "en"
    }
)


def find_descriptors(product_name, productURL, descriptors):
    # fetch the product page
    page = SESSION.get(productURL)
    soup = BeautifulSoup(page.text, 'html.parser')

    # make dataframe to store results
    df = pd.DataFrame(columns=['product', 'descriptor_type', 'descriptor', 'sentence'])

    # find paragraphs mentioning the descriptors
    for paragraph in soup.find_all('p'):
        # make text lower case and remove citations
        paragraph = paragraph.text.lower()
        paragraph = re.sub(r"\[[^\]]*\]", "", paragraph)
        for sentence in paragraph.split('. '):  # split into sentences
            for descriptor_type, descriptor_list in descriptors.items():
                for descriptor in descriptor_list:
                    if descriptor in sentence:
                        df.loc[len(df)] = [product_name, descriptor_type, descriptor, sentence]

    return df.groupby(["product", "descriptor_type"],
                      as_index=False).agg(
                          descriptors=("descriptor", lambda x: sorted(set(x))),
                          sentences=("sentence", lambda x: list(set(x))),
                          n_keyword_hits=("descriptor", "size"))


if __name__ == '__main__':
    products = pd.read_csv('data/products.csv', converters={
            'countries': ast.literal_eval,
            'countryURLs': ast.literal_eval
        })
    print('Data loaded from data/products.csv!')

    # processing and preparation descriptors
    processing_descriptors = {
        "fermented": ["fermented", "fermentation", "culture", "lactic", "probiotic", "kefir", "yogurt", "yoghurt"],
        "aged": ["aged", "ripened", "ripening", "mature", "affinage"],
        "fresh": ["fresh", "unripened"],
        "smoked": ["smoked", "smoky"],
        "cooked": ["cooked", "baked", "heated", "melted", "pasteurized", "pasteurised"]
    }

    # serving context descriptors
    serving_descriptors = {
        "breakfast": ["breakfast", "morning", "brunch", "granola", "cereal", "oatmeal", "porridge"],
        "bread": ["bread", "toast", "sandwich", "spread", "schmear", "bagel", "cracker", "crostini", "canape",
                  "canapés"],
        "dessert": ["dessert", "sweet", "cake", "pastry", "pastries", "pudding", "custard", "ice cream", "gelato",
                    "whipped", "frosting"],
        "cooking": ["cooking", "sauce", "pasta", "casserole", "gratin"],
        "snack": ["snack", "appetizer", "appetiser", "cheese board", "charcuterie", "platter", "tapas"]
    }

    # animal source descriptors
    animal_descriptors = {
        "cow": ["cow", "bovine", "jersey", "holstein"],
        "goat": ["goat", "caprine", "chèvre", "chevre"],
        "sheep": ["sheep", "ewe", "ovine"],
        "buffalo": ["buffalo", "bufala"],
        "plant_based": ["plant-based", "plant based", "vegan", "non-dairy", "non dairy", "dairy-free", "dairy free",
                        "oat milk", "soy milk", "soya milk", "almond milk", "coconut milk", "cashew milk", "rice milk",
                        "pea milk"]
    }

    # extract descriptors
    processing_df = pd.DataFrame()
    serving_df = pd.DataFrame()
    animal_df = pd.DataFrame()

    for _, row in products.iterrows():
        product, countries, description, productURL, countryURLs = row
        print(f'Extracting descriptors for {product}...')

        processing_df = pd.concat([processing_df, find_descriptors(product, productURL, processing_descriptors)],
                                  ignore_index=True)
        serving_df = pd.concat([serving_df, find_descriptors(product, productURL, serving_descriptors)],
                               ignore_index=True)
        animal_df = pd.concat([animal_df, find_descriptors(product, productURL, animal_descriptors)],
                              ignore_index=True)

    processing_df.to_csv('data/processing_descriptors.csv', sep=',', index=False)
    print('Processing descriptors saved to data/processing_descriptors.csv')
    serving_df.to_csv('data/serving_descriptors.csv', sep=',', index=False)
    print('Serving descriptors saved to data/serving_descriptors.csv')
    animal_df.to_csv('data/animal_descriptors.csv', sep=',', index=False)
    print('Animal descriptors saved to data/animal_descriptors.csv')
