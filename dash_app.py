from dash import Dash
import dash_html_components as html
import dash_core_components as dcc

import backtrader as bt

# my_app = Dash('my_app')

class RSIStrategy(bt.Strategy):

    rsi_signal = False
    macd_signal = False

    period = 0
    take_profit = 5
    stop_loss = 2

    def __init__(self):
        self.rsi = bt.talib.RSI(self.data, period=14)
        self.t_macd = bt.talib.MACD(self.data.close, fastperiod=12, slowperiod=26, signalperiod=9)

    def next(self):
        if self.t_macd.macdsignal[-1] > self.t_macd.macd[-1] and self.t_macd.macdsignal < self.t_macd.macd:
            self.macd_signal = True

        if self.rsi <= 41:
            self.rsi_signal = True

        if not self.position and self.rsi_signal and self.macd_signal:
            self.buy(size=10)

            self.rsi_signal = False
            self.macd_signal = False

        if self.position and (self.data.close > self.data.close[-1] * (100 + self.take_profit) / 100 or
                              self.data.close < self.data.close[-1] * (100 - self.stop_loss) / 100 ):
            self.close()

        if not self.position and (self.rsi_signal or self.macd_signal):
            self.period += 1

        if self.period > 3:
            self.period = 0

cerebro = bt.Cerebro()
cerebro.addstrategy(RSIStrategy)

data = bt.feeds.GenericCSVData(dataname='datasets/daily/FOXA.csv', dtformat='%Y-%m-%d')
cerebro.adddata(data)
cerebro.run()
cerebro.plot(iplot=False)