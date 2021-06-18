import os, csv
import yfinance as yf
import pandas as pd
import talib

from flask import Flask, render_template, request
from patterns import patterns

from settings import proxies

app = Flask(__name__)


@app.route('/')
def index():
    pattern = request.args.get('pattern', None)
    stocks = {}

    with open('datasets/companies.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'company': row[1], 'patterns': {}, 'signal': 0}

    if pattern:
        datafiles = os.listdir('datasets/daily')
        for filename in datafiles:
            df = pd.read_csv(f'datasets/daily/{filename}')
            pattern_function = getattr(talib, pattern)

            symbol = filename.split('.csv')[0]
            try:
                result = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = result.tail(1).values[0]
                if last > 0:
                    stocks[symbol]['patterns'][pattern] = 'bullish'
                    stocks[symbol]['signal'] = last
                elif last < 0:
                    stocks[symbol]['patterns'][pattern] = 'bearish'
                    stocks[symbol]['signal'] = last
                else:
                    stocks[symbol]['patterns'][pattern] = None
            except:
                pass

    return render_template('index.html', patterns=patterns, stocks=stocks, current_pattern=pattern)

@app.route('/multi')
def multi():
    current_pattern = request.args.get('pattern', None)
    stocks = {}

    with open('datasets/companies.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'company': row[1], 'patterns': {}, 'signal': 0}

    datafiles = os.listdir('datasets/daily')
    for filename in datafiles:
        df = pd.read_csv(f'datasets/daily/{filename}')

        for i, pattern in enumerate(patterns):
            pattern_function = getattr(talib, pattern)

            symbol = filename.split('.csv')[0]
            try:
                result = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = result.tail(1).values[0]
                if last > 0:
                    stocks[symbol]['patterns'][pattern] = 'bullish'
                    stocks[symbol]['signal'] += 100 if pattern == current_pattern else 1
                elif last < 0:
                    stocks[symbol]['patterns'][pattern] = 'bearish'
                    stocks[symbol]['signal'] -= 100 if pattern == current_pattern else 1
                else:
                    stocks[symbol]['patterns'][pattern] = None
            except:
                pass

        print(f'{symbol}: {stocks[symbol]["signal"]}')

    stocks = sorted(stocks.items(), key=lambda x: x[1]['signal'], reverse=True)

    return render_template('index.html', patterns=patterns, stocks=stocks, current_pattern=current_pattern)


@app.route('/snapshot')
def snapshot():
    with open('datasets/companies.csv') as f:
        companies = f.read().splitlines()
        for company in companies:
            symbol = company.split(',')[0]
            df = yf.download(symbol, start="2021-01-01", end="2021-06-18", proxy=proxies)
            filename = 'datasets/daily/{}.csv'.format(symbol)
            df.to_csv(filename)
            print(f'File {filename} saved')

    return {
        'code': 'success'
    }


if __name__ == '__main__':
    app.run()