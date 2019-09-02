import logging
import pandas as pd
from flask import Flask, render_template

from utils import read_config

CONFIG = read_config('config.ini')

app = Flask(__name__)

logging.basicConfig(
    filename=CONFIG['LOGFILE'],
    level=CONFIG['LOG_LEVEL'].upper(),
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S')


@app.route('/')
def index():
    logging.info('Index route called')
    return render_template('index.html')


@app.route('/predict/')
def predict_something():
    logging.info('Predict route called')
    return "Its a boat"


@app.route('/table/')
def show_table():
    logging.info('Table route called.')
    df = pd.read_csv('data/unemployment_rates.csv')
    html = df.to_html(
        header="true",
        table_id="table",
        max_rows=100,
        border=1,
        classes="table-responsive")
    return html


if __name__ == '__main__':
    app.run()
