import json
import logging
from subprocess import run, PIPE

import pandas as pd

from flask import Flask, render_template, request, redirect, url_for
from bokeh.embed import json_item
from bokeh.resources import CDN

from modeling import build_simple_model_df
from process_data import process_data
from utils import read_config
from viz import make_map_plot

CONFIG = read_config('config.ini')

app = Flask(__name__)

logging.basicConfig(
    filename=CONFIG['LOGFILE'],
    level=CONFIG['LOG_LEVEL'].upper(),
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S')


#@app.route('/')
#def index():
#    logging.info('Index route called')
#    return render_template('index.html')


@app.route('/predict/')
def predict_something():
    logging.info('Predict route called')
    return "Its a boat"


@app.route('/')
def show_table():
    logging.info('Table route called.')
    df = pd.read_parquet('data/processed_data/processed_dataset.parquet')
    html = df.to_html(
        header="true",
        table_id="dataTable",
        max_rows=100,
        classes="display")
    return render_template('index.html', table_html=html)


@app.route('/map_plot')
def show_plot():
    p = make_map_plot(year=int(CONFIG['PLOT_YEAR']))
    logging.info(f'config: {CONFIG}')
    return json.dumps(json_item(p, 'myplot'))


@app.route('/refresh_data/')
def refresh_data():
    # call shell script function
    run(['./get_data.sh'], stdout=PIPE, stderr=PIPE)
    process_data()
    build_simple_model_df()
    return render_template('index.html')


@app.route('/switch_year/', methods=['POST'])
def switch_year():
    year = request.form.get('year')
    logging.info(f'Switch year route called with arg: {year}')
    # overwrite PLOT_YEAR config var and redirect to show_plot
    logging.info(f'year: {year}')
    CONFIG['PLOT_YEAR'] = int(year)
    # call function that re-calculates data set here
    return redirect(url_for('show_plot'))

if __name__ == '__main__':
    app.run()
