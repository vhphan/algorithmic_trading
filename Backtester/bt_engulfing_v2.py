"""
Version 2
1) After EMA crossover, look for bullish engulfing
2) Buy at 1 SD (small MA window) below Engulfing low

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import math
import random
import statistics

import backtrader as bt
import matplotlib
from backtrader.indicators import EMA
import json
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.instruments as instruments
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
from oandapyV20.exceptions import V20Error
import oandapyV20.endpoints.trades as trades
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import pandas as pd
from backtrader.analyzers import SQN
from keys import oanda_keys
import matplotlib.pyplot as plt

def get_historical_data(instrument, params):
    # Create a Data Feed
    accountID = oanda_keys['account_id']
    client = API(access_token=oanda_keys['access_token'])

    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    response = client.request(r)
    print("Request: {}  #candles received: {}".format(r, len(r.response.get('candles'))))
    candles = [candle['mid'] for candle in response['candles']]
    ts = [candle['time'] for candle in response['candles']]
    vol = [candle['volume'] for candle in response['candles']]
    candles_df = pd.DataFrame(data=candles)
    ts_df = pd.DataFrame(data=ts)
    vol_df = pd.DataFrame(data=vol)
    df = pd.concat([ts_df, candles_df, vol_df], axis=1)
    df.columns = ['datetime', 'close', 'high', 'low', 'open', 'volume']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    for col in df.columns:
        df[col] = pd.to_numeric(df[col])
    print(df.head())
    return df


def get_instruments():
    accountID = oanda_keys['account_id']
    client = API(access_token=oanda_keys['access_token'])
    r = accounts.AccountInstruments(accountID=accountID)
    rv = client.request(r)
    print(json.dumps(rv, indent=2))
    for item in rv['instruments']:
        if 'USD_' in item['name']:
            print(item['name'])


def get_historical_data_factory(instrument, params):
    # Create a Data Feed
    accountID = oanda_keys['account_id']
    client = API(access_token=oanda_keys['access_token'])

    df_list = []

    def cnv(response):
        # for candle in response.get('candles'):
        #     print(candle)
        candles = [candle['mid'] for candle in response['candles']]
        ts = [candle['time'] for candle in response['candles']]
        vol = [candle['volume'] for candle in response['candles']]
        candles_df = pd.DataFrame(data=candles)
        ts_df = pd.DataFrame(data=ts)
        vol_df = pd.DataFrame(data=vol)

        df = pd.concat([ts_df, candles_df, vol_df], axis=1)
        df.columns = ['datetime', 'close', 'high', 'low', 'open', 'volume']
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        df_list.append(df)

    for r in InstrumentsCandlesFactory(instrument=instrument, params=params):
        # print("FACTORY REQUEST: {} {} {}".format(r, r.__class__.__name__, r.params))
        rv = client.request(r)
        cnv(rv)

    df2 = pd.concat(df_list)
    now = datetime.datetime.now()
    dt_string = now.strftime("%Y%m%d%H%M%S")
    df2.to_csv(f"data/data_{instrument}_{dt_string}.csv")

    return df2


def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total, 2)
    strike_rate = (total_won / total_closed) * 100
    # Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Strike Rate', 'Win Streak', 'Losing Streak', 'PnL Net']
    r1 = [total_open, total_closed, total_won, total_lost]
    r2 = [strike_rate, win_streak, lose_streak, pnl_net]
    # Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    # Print the rows
    print_list = [h1, r1, h2, r2]
    row_format = "{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('', *row))


def printSQN(analyzer):
    sqn = round(analyzer.sqn, 2)
    print('SQN: {}'.format(sqn))


def parse_args():
    parser = argparse.ArgumentParser(description='MultiData Strategy')

    parser.add_argument('--data', '-d',
                        default='../../datas/2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f',
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--period', default=15, type=int,
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--onlylong', '-ol', action='store_true',
                        help='Do only long operations')

    parser.add_argument('--writercsv', '-wcsv', action='store_true',
                        help='Tell the writer to produce a csv stream')

    parser.add_argument('--csvcross', action='store_true',
                        help='Output the CrossOver signals to CSV')

    parser.add_argument('--cash', default=100000, type=int,
                        help='Starting Cash')

    parser.add_argument('--comm', default=2, type=float,
                        help='Commission for operation')

    parser.add_argument('--mult', default=10, type=int,
                        help='Multiplier for futures')

    parser.add_argument('--margin', default=2000.0, type=float,
                        help='Margin for each future')

    parser.add_argument('--stake', default=1, type=int,
                        help='Stake to apply in each operation')

    parser.add_argument('--plot', '-p', action='store_true',
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,
                        help='Plot using numfigs figures')

    return parser.parse_args()


class Engulfing2(bt.Strategy):
    params = dict(window_s=21,
                  window_m=40,
                  window_l=200,
                  window_xs=5,
                  risk=0.05,
                  stop_dist=0.05,
                  devfactor=2
                  )

    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        dt1 = self.data0.datetime.time(0)

        # print('%s, %s' % (dt.isoformat(), txt))
        print('%s,%s, %s' % (dt.isoformat(), dt1.isoformat(), txt))

    def __init__(self):

        # custom parameter
        self.std_scale = 2
        self.bar_executed = len(self)
        self.last_engulf = 0
        self.take_profit_price = 0

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Keep a reference to the "open, low, high" line in the data[0] dataseries
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # To keep track of pending orders and buy price/commission
        self.buy_order = None
        self.sell_order = None
        self.sell_order_sl = None
        self.buy_order_sl = None
        self.sell_order_tp = None
        self.buy_order_tp = None
        self.buyprice = None
        self.buycomm = None

        # using ta-lib instead
        self.ema_s = bt.talib.EMA(self.data, timeperiod=self.params.window_s)
        self.ema_m = bt.talib.EMA(self.data, timeperiod=self.params.window_m)
        self.ema_l = bt.talib.EMA(self.data, timeperiod=self.params.window_l)
        self.boll = bt.indicators.BollingerBands(period=self.p.window_s, devfactor=self.p.devfactor)
        self.std_dev = bt.indicators.StandardDeviation(period=self.p.window_s)

        self.engulfing = bt.talib.CDLENGULFING(self.dataopen, self.datahigh, self.datalow, self.dataclose)
        self.ema_s.csv = True
        self.ema_m.csv = True
        self.ema_l.csv = True
        self.engulfing.csv = True
        self.boll.csv = True
        self.engulfing.plotinfo.subplot = True
        self.bull_cross = bt.ind.CrossOver(self.ema_m, self.ema_l)

        self.ema_s.plotinfo.plot = False
        self.boll.plotinfo.plot = False
        self.std_dev.plotinfo.plot = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.buy_order = None
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            self.bar_executed = len(self)
            self.sell_order_sl = None
            self.sell_order_tp = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        cash = self.broker.get_cash()
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.sell_order_tp or self.sell_order_sl or self.buy_order:
            return

        # Check if we are in the market
        if not self.position:
            # print('position false \n', self.position)

            # check if crossover within last window_s period
            bull_cross_recent = False
            bear_cross_recent = False
            for i in (range(-self.p.window_s + 1, 1, 1)):
                if self.bull_cross[i] == 1:
                    bull_cross_recent = True
                    bear_cross_recent = False
                elif self.bull_cross[i] == -1:
                    bull_cross_recent = False
                    bear_cross_recent = True

            # Not yet ... we MIGHT BUY if ...
            # if self.engulfing == 100 and bull_cross_recent:
            #     stdev1 = (self.boll.lines.mid[0] - self.boll.lines.bot[0]) / 2
            #     stdev2 = statistics.stdev(self.data.get(size=self.p.window_s))
            #     print(stdev1, stdev2, abs(stdev2 - stdev1))
            #     print('std indicator = ', self.std)
            #     # stop_price = self.data.close[0] - 2 * stdev2
            #     # take_profit_price = self.data.close[0] + 2 * 2 * stdev2
            #
            #     scale = 2
            #     stop_price = self.data.close[0] - stdev2 * scale
            #     take_profit_price = self.data.close[0] + 2 * stdev2 * scale
            #
            #     print(stop_price, take_profit_price, take_profit_price - stop_price)
            #
            #     # qty = math.floor((cash * self.p.risk) / (self.data.close[0] - stop_price))
            #     qty = math.floor((cash * self.p.risk) / (self.data.close[0]))
            #
            #     self.buy_order = self.buy(size=qty)
            #
            #     self.sell_order_sl = self.sell(exectype=bt.Order.Stop, size=qty, price=stop_price)
            #     self.sell_order_sl.addinfo(name='stop-loss')
            #     self.sell_order_tp = self.sell(exectype=bt.Order.Limit,
            #                                    size=qty,
            #                                    price=take_profit_price,
            #                                    oco=self.sell_order_sl)
            #     self.sell_order_tp.addinfo(name='take-profit')
            #
            #     # self.sell(exectype=bt.Order.Stop, size=qty, price=stop_price)
            #
            #     self.log('BUY CREATE, %.2f' % self.dataclose[0])
            #     self.log(f'BUY QUANTITY = {qty}')
            #     self.log('Engulf %.0f' % self.last_engulf)
            #     self.log(f'ema_s={self.ema_s[0]} ema_m={self.ema_m[0]}')
            #
            #     # Keep track of the created order to avoid a 2nd order
            #     # self.order = self.buy()

            if self.engulfing == -100 and bear_cross_recent:
                stdev1 = (self.boll.lines.mid[0] - self.boll.lines.bot[0]) / 2
                stdev2 = statistics.stdev(self.data.get(size=self.p.window_s))
                print(stdev1, stdev2, abs(stdev2 - stdev1))
                print('std indicator = ', self.std_dev[0])
                # stop_price = self.data.close[0] - 2 * stdev2
                # take_profit_price = self.data.close[0] + 2 * 2 * stdev2

                stop_price = self.data.close[0] + self.std_dev[0] * self.std_scale
                take_profit_price = self.data.close[0] - 2 * self.std_dev[0] * self.std_scale

                print(stop_price, take_profit_price, take_profit_price - stop_price)

                # qty = math.floor((cash * self.p.risk) / (self.data.close[0] - stop_price))
                qty = math.floor((cash * self.p.risk) / (self.data.close[0]))

                self.sell_order = self.sell(size=qty)
                self.buy_order_sl = self.buy(exectype=bt.Order.Stop, size=qty, price=stop_price)
                self.buy_order_sl.addinfo(name='stop-loss')
                self.buy_order_tp = self.buy(exectype=bt.Order.Limit,
                                             size=qty,
                                             price=take_profit_price,
                                             oco=self.buy_order_sl)
                self.buy_order_tp.addinfo(name='take-profit')

                # self.sell(exectype=bt.Order.Stop, size=qty, price=stop_price)

                self.log('SHORT SELL CREATE, %.2f' % self.dataclose[0])
                self.log(f'SELL QUANTITY = {qty}')
                self.log('Engulf %.0f' % self.last_engulf)
                self.log(f'ema_s={self.ema_s[0]} ema_m={self.ema_m[0]}')

                # Keep track of the created order to avoid a 2nd order
                # self.order = self.buy()




        else:
            print('position true \n', self.position)
            # if self.last_engulf == -100 and self.ema_s[0] < self.ema_m[0]:
            if self.data.close[0] >= self.take_profit_price > 0 and self.position.size > 0:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                # self.sell_order = self.sell(size=self.position.size)
                # self.log('Engulf %.0f' % self.last_engulf)
                # self.log(f'ema_s={self.ema_s[0]} ema_m={self.ema_m[0]}')


def run_strategy(strategy):
    session_id = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    timestamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')

    # parse arguments
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro()
    cerebro.addanalyzer(SQN)
    cerebro.addwriter(bt.WriterFile, out=f'output/test_{timestamp}.csv', csv=True, rounding=2)

    # oanda method 1
    # params = {
    #     "from": "2018-01-01T00:00:00Z",
    #     "granularity": "H4",
    #     "includeFirst": True,
    #     "count": 5000,
    # }
    # df = get_historical_data(instrument, params)

    # oanda method 1 (instrument factory)
    params = {
        "from": "2013-01-01T00:00:00Z",
        "granularity": "H4",
        "to": "2018-01-01T00:00:00Z"
    }
    # instrument = "EUR_USD"
    instrument = "USD_GBP"
    # df = get_historical_data_factory(instrument, params)
    df = pd.read_csv('data/data_GBP_USD_20191111160354.csv', parse_dates=True, index_col='datetime')
    df = df.loc['2014-01-01':'2017-01-01']
    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, compression=240)

    # data = bt.feeds.Quandl(
    #     dataname='F',
    #     fromdate=datetime(2016, 1, 1),
    #     todate=datetime(2017, 1, 1),
    #     buffered=True,
    #     # apikey="4EhsKT7RXXew8FU"
    # )
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    cerebro.broker.set_shortcash(False)
    # Add a strategy
    cerebro.addstrategy(strategy)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Add the analyzers we are interested in
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    # Run over everything
    strategies = cerebro.run()
    firstStrat = strategies[0]

    # print the analyzers
    printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
    printSQN(firstStrat.analyzers.sqn.get_analysis())

    # Get final portfolio Value
    portvalue = cerebro.broker.getvalue()

    # Print out the final result
    print('Final Portfolio Value: ${}'.format(portvalue))

    plt.style.use('seaborn-darkgrid')
    result = cerebro.plot(style='candlestick',
                          legendindloc='upper right',
                          legendloc='upper right',
                          legenddataloc='upper right',
                          grid=False,
                          fmt_x_ticks='%Y-%m',
                          subplot=True,
                          dpi=600
                          )


if __name__ == '__main__':
    # get_instruments()
    run_strategy(Engulfing2)
