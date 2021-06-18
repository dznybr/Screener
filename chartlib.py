import os
import pandas as pd


def is_consolidating(df, window=15, percentage=2):
    recent_candlesticks = df[-window:]
    max_close = recent_candlesticks['Close'].max()
    min_close = recent_candlesticks['Close'].min()

    threshold = 1 - (percentage / 100)
    if min_close > (max_close * threshold):
        return True


def is_breaking_out(df, window=15, percentage=2):
    last_close = df[-1:]['Close'].values[0]
    if is_consolidating(df[:-1], percentage):
        recent_candlesticks = df[-(window+1):-1]
        if last_close > recent_candlesticks['Close'].max():
            return True

    return False


datafiles = os.listdir('datasets/daily')
for filename in datafiles:
    df = pd.read_csv(f'datasets/daily/{filename}')
    if len(df) == 0:
        continue

    percentage = 2
    window = 21

    if is_consolidating(df, window=window, percentage=percentage):
        print(f'{filename} is consolidating')

    if is_breaking_out(df, window=window, percentage=percentage):
        print(f'{filename} is breaking out')
