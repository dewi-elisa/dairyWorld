import pandas as pd
import ast
import plotly.express as px
import country_converter as coco
import logging
logging.getLogger("country_converter.country_converter").setLevel(logging.ERROR)


def country2iso3(countries):
    iso3_codes = []
    for country in countries:
        # convert country to iso3
        iso3 = coco.convert(names=country, to='ISO3')
        # check if conversion was successful, if not, add manually
        if iso3 != 'not found':
            iso3_codes.append(iso3)
        else:
            country2iso3_mapping = {
                'USSR': coco.convert(names='Russia', to='ISO3'),
                'Khan garh': coco.convert(names='Pakistan', to='ISO3'),
                'Scotland': coco.convert(names='United Kingdom', to='ISO3'),
                'Vikings': coco.convert(names='United Kingdom', to='ISO3'),
                'Central Asia': coco.convert(names='Kazakhstan', to='ISO3'),
                'West Sumatra': coco.convert(names='Indonesia', to='ISO3'),
                'Scandinavia': coco.convert(names=['Sweden', 'Norway', 'Denmark'], to='ISO3'),
                'Alps': coco.convert(names='Switzerland', to='ISO3'),
                'Andhra Pradesh': coco.convert(names='India', to='ISO3'),
                'Caucasus': coco.convert(names='Georgia', to='ISO3'),
                'Punjab': coco.convert(names=['India', 'Pakistan'], to='ISO3'),
                'Central and Eastern Europe': coco.convert(names='Poland', to='ISO3'),
                'Mannheim': coco.convert(names='Germany', to='ISO3'),
                'Minoru Shirota': coco.convert(names='Japan', to='ISO3'),
            }
            if isinstance(country2iso3_mapping[country], list):
                iso3_codes.extend(country2iso3_mapping[country])
            else:
                iso3_codes.extend([country2iso3_mapping[country]])
    return set(iso3_codes)


def make_world_df(products):
    # explode the dataframe by iso3 codes
    df = products.explode("iso3").copy()

    # group by iso3 codes and aggregate dairy products and scores
    map_df = df.groupby("iso3", as_index=False).agg(
        dairy_product=("product", lambda s: sorted(set(s))),
        score=("product", lambda s: s.nunique()),
    )

    # format dairy products as semicolon-separated string
    map_df["dairy_product(s)"] = map_df["dairy_product"].apply(lambda lst: "; ".join(lst))

    # convert iso3 codes back to country names for hover info
    map_df["country"] = coco.convert(names=map_df["iso3"].tolist(), to="name_short")

    return map_df


if __name__ == '__main__':
    products = pd.read_csv('data/products.csv', converters={
            'countries': ast.literal_eval,
            'countryURLs': ast.literal_eval
        })
    print('Data loaded from data/products.csv!')

    print('Mapping countries to ISO3 codes...')
    products['iso3'] = products['countries'].apply(country2iso3)

    print('Creating world map dataframe...')
    map_df = make_world_df(products)
    print(map_df.head())

    print('Creating world map...')
    fig = px.choropleth(
        map_df,
        locations="iso3",
        color="score",
        range_color=(1, 7),
        color_continuous_scale=px.colors.sequential.Oranges,
        hover_name="country",
        hover_data={"dairy_product(s)": True, "score": False, "iso3": False},
        projection="natural earth",
        labels={"score": "Number of products"},
    )

    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    fig.show()
    fig.write_html("results/world_map.html")
    print("Saved to results/world_map.html")
    print('Done!')
