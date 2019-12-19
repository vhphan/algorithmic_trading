from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import backtrader as bt
from helpers import my_position_size
from my_indicators import SpecialEMA

DEFAULT_PARAMS = dict(window_s=21, window_m=50, window_l=100, window_xs=5, risk=0.05, stop_dist=0.05, dev_factor=2)


class GenericStrategy(bt.Strategy):
    params = DEFAULT_PARAMS

    def __init__(self):
        # custom parameter
        timestamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
        cn = self.__class__.__name__

        self.csv_file = f'output/{cn}-{timestamp}-bt-run.csv'
        self.std_scale = self.params.dev_factor

        # To keep track of pending orders and buy price/commission
        self.order_refs = dict()
        self.buy_order = dict()
        self.sell_order = dict()
        self.indicators = dict()

    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        dt1 = self.data0.datetime.time(0)

        # print('%s, %s' % (dt.isoformat(), txt))
        print('%s,%s, %s' % (dt.isoformat(), dt1.isoformat(), txt))

    def setup_csv_file(self, add_header=None):
        """
        Function to setup csv file to log the strategy execution.
        The file can then be analyzed with pandas later.
        """

        if add_header is None:
            add_header = []
        basic_header = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        # Write the header to the trade log.
        header = basic_header + add_header

        with open(self.csv_file, 'w') as file:
            file.write(','.join(header) + "\n")

    def notify_order(self, order):

        dt, dn = self.datetime.date(), order.data._name
        print('{} {} Order {} Status {}'.format(
            dt, dn, order.ref, order.getstatusname())
        )

        if not order.alive():
            for i, d in enumerate(self.datas):
                if order.ref in self.order_refs[d._name]:
                    self.order_refs[d._name].remove(order.ref)

        print('{}: Order ref: {} / Type {} / Status {} / Instrument {}'.format(
            self.data.datetime.datetime(0),
            order.ref, 'Buy' * order.isbuy() or 'Sell',
            order.getstatusname(),
            self.data._name))

        if order.status == order.Completed:
            print('order completed')

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

        # for item in self.indobscsv:
        #     print(type(item))
        #     print(getattr(item, '__module__', None))

    # from https://backtest-rookies.com/2017/06/06/code-snippet-forex-position-sizing/
    def size_position(self, price, stop, risk, method=0, exchange_rate=None, jpy_pair=False):
        """
        Helper function to calcuate the position size given a known amount of risk.

        *Args*
        - price: Float, the current price of the instrument
        - stop: Float, price level of the stop loss
        - risk: Float, the amount of the account equity to risk

        *Kwargs*
        - JPY_pair: Bool, whether the instrument being traded is part of a JPY
        pair. The muliplier used for calculations will be changed as a result.
        - Method: Int,
            - 0: Acc currency and counter currency are the same
            - 1: Acc currency is same as base currency
            - 2: Acc currency is neither same as base or counter currency
        - exchange_rate: Float, is the exchange rate between the account currency
        and the counter currency. Required for method 2.

        Return value of units to buy/sell. To convert to lot:
        units/100_000 = # of lots
        units/10_000 = # of mini lots
        units/1_000 = # of micro lots
        """

        if jpy_pair:  # check if a YEN cross and change the multiplier
            multiplier = 0.01
        else:
            multiplier = 0.0001

        # Calc how much to risk
        acc_value = self.broker.getvalue()
        cash_risk = acc_value * risk
        stop_pips_int = abs((price - stop) / multiplier)  # number of pips between price and stop
        pip_value = cash_risk / stop_pips_int

        if method == 1:
            # pip_value = pip_value * price
            units = pip_value / multiplier
            return units

        elif method == 2:
            pip_value = pip_value * exchange_rate
            units = pip_value / multiplier
            return units

        else:  # is method 0
            units = pip_value / multiplier
            return units
