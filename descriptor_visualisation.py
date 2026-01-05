import pandas as pd
import ast
import matplotlib.pyplot as plt


def determine_descriptor(df, products):
    descriptor = pd.DataFrame(columns=['product', 'descriptor'])

    # find descriptor with most keyword hits per product
    for product in products:
        product_df = df[df['product'] == product]
        if len(product_df) == 0:
            descriptor.loc[len(descriptor)] = [product, 'none']
        else:
            max_hits = product_df['n_keyword_hits'].max()
            top_descriptors = product_df[product_df['n_keyword_hits'] == max_hits]
            for _, row in top_descriptors.iterrows():  # if tie: add all
                descriptor.loc[len(descriptor)] = [product, row['descriptor_type']]

    return descriptor


def visualize_descriptor(df, products, descriptors, file_name):
    N = len(products)
    df = determine_descriptor(df, products)
    df = df.value_counts('descriptor')

    # make it percentages
    df = (df / N) * 100

    # check if all descriptors are present, if not add them with 0%
    for descriptor in descriptors:
        if descriptor not in df.index:
            df.loc[descriptor] = 0.0

    # make barplot and save
    ax = df.plot.bar(color='orange')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.set_xlabel('')
    ax.set_ylabel('%')
    ax.set_title('')
    ax.tick_params(axis='x', labelrotation=0)

    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()


if __name__ == '__main__':
    products = pd.read_csv('data/products.csv', converters={
            'countries': ast.literal_eval,
            'countryURLs': ast.literal_eval
        })
    print('Data loaded from data/products.csv!')

    processing = pd.read_csv('data/processing_descriptors.csv', converters={
            'descriptors': ast.literal_eval,
            'sentences': ast.literal_eval
        })
    print('Data loaded from data/processing_descriptors.csv!')
    visualize_descriptor(processing,
                         products['product'],
                         ['fermented', 'aged', 'fresh', 'smoked', 'cooked'],
                         'results/processing_descriptors_visualization.png')
    print('Visualized processing descriptors in results/processing_descriptors_visualization.csv!')

    serving = pd.read_csv('data/serving_descriptors.csv', converters={
            'descriptors': ast.literal_eval,
            'sentences': ast.literal_eval
        })
    print('Data loaded from data/serving_descriptors.csv!')
    visualize_descriptor(serving,
                         products['product'],
                         ['breakfast', 'bread', 'dessert', 'cooking', 'snack'],
                         'results/serving_descriptors_visualization.png')
    print('Visualized serving descriptors in results/serving_descriptors_visualization.csv!')

    animal = pd.read_csv('data/animal_descriptors.csv', converters={
            'descriptors': ast.literal_eval,
            'sentences': ast.literal_eval
        })
    print('Data loaded from data/animal_descriptors.csv!')
    visualize_descriptor(animal,
                         products['product'],
                         ['cow', 'goat', 'sheep', 'buffalo', 'plant_based'],
                         'results/animal_descriptors_visualization.png')
    print('Visualized animal source descriptors in results/animal_descriptors_visualization.csv!')
