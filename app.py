import os, csv
import yfinance as yf
import pandas as pd
import talib

from flask import Flask, render_template, request, redirect, flash, jsonify
from patterns import patterns
from binance.client import Client
from binance.enums import *
from datetime import datetime

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

    with open('datasets/ruspanies.csv') as f:
        for row in csv.reader(f):
            stocks_list[row[0]] = row[1]

    if pattern == 'RSI_MACD_LONG' or pattern == 'RSI_MACD_SHORT':

        interval = 6

        rsi_length = 14
        rsi_oversold = 30
        rsi_overbought = 70

        macd_fast = 12
        macd_slow = 26
        mac_signal = 9

        EMA_Green_TimePeriod = 13
        EMA_Red_TimePeriod = 8
        EMA_Blue_TimePeriod = 5

        EMA_Green_Offset = 8
        EMA_Red_Offset = 5
        EMA_Blue_Offset = 3

        if request.method == "POST":
            interval = int(request.form.get("interval", interval))

            rsi_length = int(request.form.get("rsi_length", rsi_length))
            rsi_oversold = int(request.form.get("rsi_oversold", rsi_oversold))
            rsi_overbought = int(request.form.get("rsi_overbought", rsi_overbought))

            macd_fast = int(request.form.get("macd_fast", macd_fast))
            macd_slow = int(request.form.get("macd_slow", macd_slow))
            mac_signal = int(request.form.get("mac_signal", mac_signal))

            EMA_Green_TimePeriod = int(request.form.get("EMA_Green_TimePeriod", EMA_Green_TimePeriod))
            EMA_Red_TimePeriod = int(request.form.get("EMA_Red_TimePeriod", EMA_Red_TimePeriod))
            EMA_Blue_TimePeriod = int(request.form.get("mac_signal", EMA_Blue_TimePeriod))

            EMA_Green_Offset = int(request.form.get("EMA_Green_Offset", EMA_Green_Offset))
            EMA_Red_Offset = int(request.form.get("EMA_Red_Offset", EMA_Red_Offset))
            EMA_Blue_Offset = int(request.form.get("EMA_Blue_Offset", EMA_Blue_Offset))

            print(f'request.form: {request.form}')
            print('Got parameters from form')

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

        datafiles = os.listdir('datasets/daily_ru')
        for filename in datafiles:

            df = pd.read_csv(f'datasets/daily_ru/{filename}')
            if df.empty:
                continue

            symbol = filename.split('.csv')[0]
            # print(f'Analyzing  {symbol}')

            rsi = talib.RSI(df['Close'], timeperiod=rsi_length)
            macd, macdsignal, _ = talib.MACD(df['Close'], fastperiod=macd_fast, slowperiod=macd_slow, signalperiod=mac_signal)

            # Alligator EMA
            df['EMA_green'] = talib.EMA(df['Close'], timeperiod=EMA_Green_TimePeriod)
            df['EMA_red'] = talib.EMA(df['Close'], timeperiod=EMA_Red_TimePeriod)
            df['EMA_blue'] = talib.EMA(df['Close'], timeperiod=EMA_Blue_TimePeriod)

            df['EMA_green'] = pd.to_numeric(df['EMA_green'].shift(periods=EMA_Green_Offset))
            df['EMA_red'] = pd.to_numeric(df['EMA_red'].shift(periods=EMA_Red_Offset))
            df['EMA_blue'] = pd.to_numeric(df['EMA_blue'].shift(periods=EMA_Blue_Offset))

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

                if pattern == 'RSI_MACD_LONG' and previous_macdsignal > previous_macd and current_macdsignal < current_macd or \
                   pattern == 'RSI_MACD_SHORT' and previous_macdsignal < previous_macd and current_macdsignal > current_macd :
                    macd_signal = True
                    macd_value = current_macd
                    macdsignal_value = current_macdsignal
                    macd_offset = 1-i
                    macd_price = df["Close"][len(df)-i]

                if macd_signal and pattern == 'RSI_MACD_LONG' and previous_macdsignal < previous_macd and current_macdsignal > current_macd or \
                   macd_signal and pattern == 'RSI_MACD_SHORT' and previous_macdsignal > previous_macd and current_macdsignal < current_macd :
                    macd_signal = False
                    macd_value = 0
                    macdsignal_value = 0
                    macd_offset = 0

                current_rsi = rsi[len(rsi)-i]
                if pattern == 'RSI_MACD_LONG' and current_rsi < rsi_oversold or \
                   pattern == 'RSI_MACD_SHORT' and current_rsi > rsi_overbought:
                    rsi_signal = True
                    rsi_value = current_rsi
                    rsi_offset = 1-i
                    rsi_price = df["Close"][len(df)-i]

                if rsi_signal and pattern == 'RSI_MACD_LONG' and current_rsi > rsi_oversold or \
                   rsi_signal and pattern == 'RSI_MACD_SHORT' and current_rsi < rsi_overbought:
                    rsi_signal = False
                    rsi_value = 0
                    rsi_offset = 0

            if rsi_signal and macd_signal:
                stocks[symbol] = {'company': stocks_list[symbol],
                                  'macd': macd_value,
                                  'macdsignal': macdsignal_value,
                                  'macd_offset': macd_offset,
                                  'macd_price': macd_price,
                                  'rsi': rsi_value,
                                  'rsi_offset': rsi_offset,
                                  'rsi_price': rsi_price
                                  }

                print(f'Company {symbol}: rsi({rsi_offset}){rsi_value}[{rsi_price}], macd({macd_offset}){macd_value}[{macd_price}], macdsignal({macd_offset}){macdsignal_value}[]')

#            except:
#                pass

    return render_template('index_2.html', patterns=patterns, stocks=stocks, current_pattern=pattern, params=params)

@app.route('/snapshot')
def snapshot():
    with open('datasets/ruspanies.csv') as f:
        companies = f.read().splitlines()
        for company in companies:
            symbol = company.split(',')[0]
            print(symbol)
            df = yf.download(symbol, start="2021-01-01", end=datetime.strftime(datetime.now().date(),'%Y-%m-%d'), proxy=proxies)
            if df.empty:
                df = yf.download(f'{symbol}.ME', start="2021-01-01", end=datetime.strftime(datetime.now().date(),'%Y-%m-%d'), proxy=proxies)
            filename = 'datasets/daily_ru/{}.csv'.format(symbol)
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