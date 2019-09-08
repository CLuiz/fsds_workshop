from bokeh.io import show
from bokeh.models import LogColorMapper
from bokeh.palettes import Viridis6 as palette
from bokeh.plotting import figure

from bokeh.sampledata.us_counties import data as counties
from bokeh.sampledata.unemployment import data as unemployment

import pandas as pd

from modeling import build_simple_model_df

def make_map_plot(
    counties=counties, data=unemployment, year=2018, additional_data=True):
    # examples directory: http://bokeh.pydata.org/en/latest/docs/gallery/
    # example adapted from http://bokeh.pydata.org/en/latest/docs/gallery/texas.html

    # changes color pallete assignments
    #palette.reverse()

    # grab polygons for Colorado counties only
    counties = {
        code: county for code, county in counties.items() if county["state"] == "co"
    }

    if additional_data:
        df = build_simple_model_df(save=False)
        #df = pd.read_parquet('data/processed_data/simple_modeling_set.parquet', engine='fastparquet')
        counties_df = pd.DataFrame.from_records(counties).T
        additional_data_df = pd.merge(
            df, counties_df, how='left', left_on='county', right_on='name')
        # subset to 2018
        additional_data_df = additional_data_df[
            additional_data_df['year'] == year]

    # need to convert to this format for Bokeh to render the plot
    county_xs = [county["lons"] for county in counties.values()]
    county_ys = [county["lats"] for county in counties.values()]

    county_names = [county['name'] for county in counties.values()]

    # This is what we will need to change to adapt the map to use different values

    # county_rates = [data[county_id] for county_id in counties]
    county_rates = additional_data_df['unemprate']
    expected_consumers = additional_data_df['total_expected_consumers'] / 1000
    # maps colors to the
    color_mapper = LogColorMapper(palette=palette)


    # Bokeh expects the data in a dict as follows
    data=dict(
        x=county_xs,
        y=county_ys,
        name=county_names,
        rate=county_rates,
        customers=expected_consumers,
    )

    # all tools here: https://bokeh.pydata.org/en/latest/docs/user_guide/tools.html
    TOOLS = "pan,wheel_zoom,reset,hover,save"

    p = figure(
        # title="Colorado  Unemployment, 2009", tools=TOOLS,
        title=f"Colorado County Statistics {str(year)}", tools=TOOLS,
        # sizing_mode controls how the plot responds to browser resizing
        sizing_mode="stretch_both",
        # if you are having issues with the image fitting in the plot box,
        # you may want to adjust the width policy value
        width_policy="fit",
        # We don't need axes for this plot
        x_axis_location=None, y_axis_location=None,
        # This is the fun stuff! And so easy to implement, what do we want
        # the chart to show on hover?
        tooltips=[
            ("Name", "@name"),
            ("Unemployment rate", "@rate%"),
            ("Expected Customers (k)", "@customers"),
            ("(Long, Lat)", "($x, $y)")
        ])
    # A grid isn't going to make this easier to read, turn off
    p.grid.grid_line_color = None

    p.hover.point_policy = "follow_mouse"

    # MUST set to maintain aspect ratio of state
    p.match_aspect = True

    # patches is how polygons are passed for visualization
    p.patches('x', 'y', source=data,
              fill_color={'field': 'customers', 'transform': color_mapper},
              fill_alpha=0.7, line_color="white", line_width=0.5)

    return p
