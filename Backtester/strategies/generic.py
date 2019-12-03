from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import backtrader as bt
from helpers import position_size, my_std_scale
from my_indicators import SpecialEMA

DEFAULT_PARAMS = dict(window_s=21, window_m=50, window_l=100, window_xs=5, risk=0.05, stop_dist=0.05, devfactor=2)


class GenericStrategy(bt.Strategy):
    params = DEFAULT_PARAMS

    def __init__(self):
        # custom parameter
        self.std_scale = my_std_scale
        self.bar_executed = len(self)
        self.last_engulf = 0

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Keep a reference to the "open, low, high" line in the data[0] dataseries
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # To keep track of pending orders and buy price/commission
        self.order_refs = list()
        self.buy_order = None
        self.sell_order = None
        self.buyprice = None
        self.buycomm = None

    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        dt1 = self.data0.datetime.time(0)

        # print('%s, %s' % (dt.isoformat(), txt))
        print('%s,%s, %s' % (dt.isoformat(), dt1.isoformat(), txt))

    def notify_order(self, order):
        print('{}: Order ref: {} / Type {} / Status {}'.format(
            self.data.datetime.datetime(0),
            order.ref, 'Buy' * order.isbuy() or 'Sell',
            order.getstatusname()))

        if order.status == order.Completed:
            print('order completed')

        if not order.alive() and order.ref in self.order_refs:
            self.order_refs.remove(order.ref)

    def notify_trade(self, trade):
        date = self.data.datetime.datetime()
        if trade.isclosed:
            print('-' * 32, ' NOTIFY TRADE ', '-' * 32)
            print('{}, Entry Price: {}, Profit, Gross {}, Net {}'.format(
                date,
                trade.price,
                round(trade.pnl, 2),
                round(trade.pnlcomm, 2)))
            print('-' * 80)

    def stop(self):
        print('stopping')
        # result = list()
        # result.append(pd.DataFrame({'kijun_sen': self.ichimoku.kijun_sen.get(size=len(self.ichimoku))}))
        # result.append(pd.DataFrame({'tenkan_sen': self.ichimoku.tenkan_sen.get(size=len(self.ichimoku))}))
        # result_df = pd.concat(result, axis=1)
