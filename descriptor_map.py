import pandas as pd
import numpy as np
import ast
import plotly.graph_objects as go
import plotly.express as px
from product_origin_relation import country2iso3
from descriptor_visualisation import determine_descriptor
import country_converter as coco


def get_descriptors(df, category, products):
    # get top descriptor(s) per product
    descriptor_df = determine_descriptor(df, products)

    # give it a label for the world map
    descriptor_df['label'] = category + ': ' + descriptor_df['descriptor'].astype(str)

    # wether or not to show it for this category
    descriptor_df['show'] = descriptor_df['descriptor'].ne('none')

    return descriptor_df[['product', 'label', 'show']]


if __name__ == '__main__':
    print('Loading data...')
    products = pd.read_csv('data/products.csv', converters={
        'countries': ast.literal_eval,
        'countryURLs': ast.literal_eval
        })
    processing = pd.read_csv('data/processing_descriptors.csv')
    serving = pd.read_csv('data/serving_descriptors.csv')
    animal = pd.read_csv('data/animal_descriptors.csv')

    print('Adding ISO3 codes to product dataframe...')
    products['iso3'] = products['countries'].apply(country2iso3)

    # if there are multiple ISO3 codes per country, explode to one per row
    prod_country = (
        products[['product', 'iso3']]
        .explode('iso3')
    )

    print('Adding country names...')
    prod_country['country'] = coco.convert(names=prod_country['iso3'].tolist(), to='name_short')

    print('Adding descriptors...')
    descriptors = pd.concat(
        [get_descriptors(processing, 'processing', products['product']),
         get_descriptors(serving, 'serving', products['product']),
         get_descriptors(animal, 'animal', products['product'])],
        ignore_index=True
    )
    data = prod_country.merge(descriptors, on='product', how='left')

    print('Making hover information...')
    # total products per country
    totals = prod_country.groupby('iso3')['product'].nunique().rename('n_products')

    # numerator per (country, label)
    agg = (
        data.groupby(['iso3', 'label'])
        .agg(country=('country', 'first'), n_match=('show', 'sum'))
        .reset_index()
        .merge(totals, on='iso3', how='left')
    )
    agg['data'] = (agg['n_match'] / agg['n_products']) * 100

    # add products
    products = (
        data[data['show']]
        .groupby(['iso3', 'label'])['product']
        .apply(lambda s: ', '.join(sorted(pd.unique(s))))
        .reset_index(name='products')
    )
    agg = agg.merge(products, on=['iso3', 'label'], how='left').fillna({'products': ''})
    agg = agg[~agg['label'].str.endswith(': none')]  # do not add the none descriptors

    print('Making the world map...')
    labels = sorted(agg['label'].unique())

    fig = go.Figure()

    for i, lab in enumerate(labels):
        d = agg[agg['label'] == lab].copy()

        fig.add_trace(
            go.Choropleth(
                locations=d['iso3'],
                locationmode='ISO-3',
                z=d['data'],
                visible=(i == 0),
                coloraxis='coloraxis',
                # colorbar_title='% of products',
                customdata=np.stack([d['country'], d['n_match'], d['n_products'], d['products']], axis=-1),
                hovertemplate=(
                    '<b>%{customdata[0]}</b> (%{location})<br>'
                    + lab + '<br>'
                    + '%{z:.1f}% (%{customdata[1]}/%{customdata[2]})<br>'
                    + 'products: %{customdata[3]}'
                    + '<extra></extra>'
                )
            )
        )

    buttons = []
    for i, lab in enumerate(labels):
        vis = [False] * len(labels)
        vis[i] = True
        buttons.append(
            dict(
                label=lab,
                method='update',
                args=[{'visible': vis}]
            )
        )

    fig.update_layout(
        title=f'Descriptor prevalence by country',
        updatemenus=[dict(buttons=buttons, direction='down', x=0.02, y=0.98)],
        geo=dict(projection_type='natural earth'),
        margin=dict(l=10, r=10, t=50, b=10),
        coloraxis=dict(
            colorscale=px.colors.sequential.Oranges,
            cmin=0,
            cmax=100,
            colorbar=dict(title='% of products'))
    )
    fig.show()

    print('Saving the world map...')
    fig.write_html('results/descriptor_map_dropdown.html', include_plotlyjs=True)
    print('Done!')
