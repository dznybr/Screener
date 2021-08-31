import os, csv
import yfinance as yf
import pandas as pd
import talib

from flask import Flask, render_template, request, redirect, flash, jsonify
from patterns import patterns
from binance.client import Client
from binance.enums import *

from settings import proxies, api_key, secret_key

app = Flask(__name__)
app.secret_key = r'aslkfjqkorfalskdfmalskerjlsdfmksdfmtuj63wrtjkryiu'

client = Client(api_key, secret_key, {'proxies': proxies})

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
                    stocks[symbol]['signal'] = last
            except:
                pass

    return render_template('index.html', patterns=patterns, stocks=stocks, current_pattern=pattern)

@app.route('/multi')
def multi():
    current_pattern = request.args.get('pattern', 'ALL')
    stocks = {}

    with open('datasets/companies.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'company': row[1], 'patterns': {}, 'signal': 0}

    datafiles = os.listdir('datasets/daily')
    for filename in datafiles:
        df = pd.read_csv(f'datasets/daily/{filename}')
        stock = filename.split('.csv')[0]
        if stocks.get(stock, None) is None:
            continue

        for i, pattern in enumerate(patterns):
            pattern_function = getattr(talib, pattern)

            try:
                result = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = result.tail(1).values[0]
                if last > 0:
                    stocks[stock]['patterns'][pattern] = 'bullish'
                    stocks[stock]['signal'] += last if pattern == current_pattern else int(last/100)
                elif last < 0:
                    stocks[stock]['patterns'][pattern] = 'bearish'
                    stocks[stock]['signal'] += last if pattern == current_pattern else -int(last/100)
                else:
                    stocks[stock]['patterns'][pattern] = None
            except:
                pass

        stocks[stock]['patterns'] = {k: stocks[stock]['patterns'][k] for i, k in enumerate(stocks[stock]['patterns']) if not stocks[stock]['patterns'][k] is None}
        stocks[stock]['patterns']['ALL'] = 'bullish' if stocks[stock]['signal'] > 0 else 'bearish'

        print(f'{stock}: {stocks[stock]}')

    stocks = {k: stocks[k] for i, k in enumerate(stocks) if stocks[k]['signal'] != 0}

    stocks = dict(sorted(stocks.items(), key=lambda x: x[1]['signal'], reverse=True))

    return render_template('index.html', patterns=patterns, stocks=stocks, current_pattern=current_pattern)

@app.route('/search', methods=['GET', 'POST'])
def search():

    pattern = request.args.get('pattern', 'RSI_MACD_LONG')
    stocks = {}
    stocks_list = {}
    params = {}

    with open('datasets/companies.csv') as f:
        for row in csv.reader(f):
            stocks_list[row[0]] = row[1]

    if pattern == 'RSI_MACD_LONG' or pattern == 'RSI_MACD_SHORT':

        interval = request.form.get("interval")
        interval = 6 if interval is None else int(interval)

        rsi_length = int(request.form.get("rsi_length", 14))
        rsi_oversold = int(request.form.get("rsi_oversold", 30))
        rsi_overbought = int(request.form.get("rsi_overbought", 70))

        macd_fast = int(request.form.get("macd_fast", 12))
        macd_slow = int(request.form.get("macd_slow", 26))
        mac_signal = int(request.form.get("mac_signal", 9))

        params['interval'] = interval
        params['rsi_length'] = rsi_length
        params['rsi_oversold'] = rsi_oversold
        params['rsi_overbought'] = rsi_overbought
        params['macd_fast'] = macd_fast
        params['macd_slow'] = macd_slow
        params['mac_signal'] = mac_signal

        print(f'interval {interval}')

        print(f'rsi_length {rsi_length}')
        print(f'rsi_oversold {rsi_oversold}')
        print(f'rsi_overbought {rsi_overbought}')

        print(f'macd_fast {macd_fast}')
        print(f'macd_slow {macd_slow}')
        print(f'mac_signal {mac_signal}')

        datafiles = os.listdir('datasets/daily')
        for filename in datafiles:

            df = pd.read_csv(f'datasets/daily/{filename}')
            if df.empty:
                continue

            symbol = filename.split('.csv')[0]

            rsi = talib.RSI(df['Close'], timeperiod=rsi_length)
            macd, macdsignal, _ = talib.MACD(df['Close'], fastperiod=macd_fast, slowperiod=macd_slow, signalperiod=mac_signal)

            rsi_signal = False
            macd_signal = False

            rsi_value = 0
            macd_value = 0
            macdsignal_value = 0

            rsi_offset = 0
            macd_offset = 0

#            try:
            for i in range(1, interval+1):

                current_macd = macd[len(macd)-i]
                current_macdsignal = macdsignal[len(macd)-i]

                previous_macd = macd[len(macd)-i-1]
                previous_macdsignal = macdsignal[len(macd)-i-1]

                if pattern == 'RSI_MACD_LONG' and previous_macdsignal >= previous_macd and current_macdsignal <= current_macd or \
                   pattern == 'RSI_MACD_SHORT' and previous_macdsignal <= previous_macd and current_macdsignal >= current_macd :
                    macd_signal = True
                    macd_value = current_macd
                    macdsignal_value = current_macdsignal
                    macd_offset = 1-i

                current_rsi = rsi[len(rsi)-i]
                if pattern == 'RSI_MACD_LONG' and current_rsi < rsi_oversold or \
                   pattern == 'RSI_MACD_SHORT' and current_rsi > rsi_overbought:
                    rsi_signal = True
                    rsi_value = current_rsi
                    rsi_offset = 1-i

            if rsi_signal and macd_signal:
                stocks[symbol] = {'company': stocks_list[symbol],
                                  'macd': macd_value,
                                  'macdsignal': macdsignal_value,
                                  'macd_offset': macd_offset,
                                  'rsi': rsi_value,
                                  'rsi_offset': rsi_offset
                                  }

                print(f'Company {symbol}: rsi{rsi_offset} - {rsi_value}, macd{macd_offset} - {macd_value}, macdsignal{macd_offset} - {macdsignal_value} ')

#            except:
#                pass

    return render_template('index_2.html', patterns=patterns, stocks=stocks, current_pattern=pattern, params=params)

@app.route('/snapshot')
def snapshot():
    with open('datasets/companies.csv') as f:
        companies = f.read().splitlines()
        for company in companies:
            symbol = company.split(',')[0]
            print(symbol)
            df = yf.download(symbol, start="2021-01-01", end="2021-09-01", proxy=proxies)
            filename = 'datasets/daily/{}.csv'.format(symbol)
            df.to_csv(filename)
            print(f'File {filename} saved')

    return {
        'code': 'success'
    }

@app.route('/chart')
def chart():
    print('chart')
    return render_template('chart.html')

@app.route('/settings')
def settings():

    flash(request.form, 'error')
    print('settings')

    return redirect('/chart')

@app.route('/history')
def history():
    print('history')

    candlesticks = client.get_historical_klines('BTCUSDT', Client.KLINE_INTERVAL_15MINUTE, '23 Jun, 2021', '24 Jun, 2021')

    print('candlesticks got')
    processed_candlesticks = []

    for data in candlesticks:
        candlestick = {
            'time': int(data[0]/1000),
            'open': data[1],
            'high': data[2],
            'low':  data[3],
            'close': data[4],
        }
        processed_candlesticks.append(candlestick)

    return jsonify(processed_candlesticks)

if __name__ == '__main__':
    app.run()