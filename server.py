import json
import logging
import subprocess

import pandas as pd

from flask import Flask, render_template
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
    p = make_map_plot()
    return json.dumps(json_item(p, 'myplot'))


@app.route('/refresh_data/')
def refresh_data():
    # call shell script function
    subprocess.run(['./get_data.sh'])
    process_data()
    build_simple_model_df()
    return render_template('index.html', table_html=html)


if __name__ == '__main__':
    app.run()
