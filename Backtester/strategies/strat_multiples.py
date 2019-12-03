from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
from helpers import position_size, my_std_scale


class EngulfingMultipleInstruments(bt.Strategy):
    params = dict(window_s=21,
                  window_m=50,
                  window_l=100,
                  window_xs=5,
                  risk=0.05,
                  stop_dist=0.05,
                  devfactor=2
                  )

    def __init__(self):

        self.std_scale = my_std_scale
        self.o = dict()
        self.o_refs = dict()
        self.holding = dict()  # holding periods per data
        self.inds = dict()

        for i, d in enumerate(self.datas):
            self.o_refs[d._name] = []
            self.inds[d] = dict()
            self.inds[d]['ichimoku'] = bt.indicators.Ichimoku()
            self.inds[d]['engulfing'] = bt.talib.CDLENGULFING(d.open, d.high, d.low, d.close)
            self.inds[d]['stdev'] = bt.indicators.StandardDeviation(period=self.p.window_s)

            self.inds[d]['stdev'].subplot = False
            self.inds[d]['ichimoku'].subplot = False
            self.inds[d]['engulfing'].subplot = False

            self.inds[d]['stdev'].plotinfo.plot = False
            self.inds[d]['ichimoku'].plotinfo.plot = False
            self.inds[d]['engulfing'].plotinfo.plot = False

        print('finished init')

    def next(self):
        cash = self.broker.get_cash()
        for i, d in enumerate(self.datas):

            # self.log(f'Close, {d._name} {d[0]:.2f}')
            dt, dn = self.datetime.date(), d._name
            pos = self.getposition(d).size
            if pos > 0:
                print('{} {} Position {}'.format(dt, dn, pos))

            # if not pos and not self.o.get(d, None):
            # if self.o_refs[d._name]:
            # print(self.o_refs)

            if not pos and not self.o_refs[d._name]:

                # Long strategy here
                if self.inds[d]['engulfing'] == 100 and d[0] > self.inds[d]['ichimoku'].senkou_span_a[0] and d[0] > \
                        self.inds[d]['ichimoku'].senkou_span_b[0]:
                    stop_price = d[0] - self.inds[d]['stdev'] * self.std_scale
                    take_profit_price = d[0] + 2 * self.inds[d]['stdev'] * self.std_scale

                    qty = position_size(cash, stop_price, d[0], self.params.risk)
                    # qty = 100



                    self.o[d] = self.buy_bracket(data=d, limitprice=take_profit_price, stopprice=stop_price,
                                                 exectype=bt.Order.Market, size=qty)

                    self.o_refs[d._name] = [o.ref for o in self.o[d]]

                    self.log(f'CURRENCY {d._name}')
                    self.log(f'CURRENT CASH = {cash:.2f}')
                    self.log('BUY CREATE, %.2f' % d[0])
                    self.log(f'BUY QUANTITY = {qty}')
                    self.log(f'SL PRICE = {stop_price}')
                    self.log(f'TP PRICE = {take_profit_price}')
                    self.log(f'CURRENT PRICE = {d[0]}')

                if self.inds[d]['engulfing'] == -100 and d[0] < self.inds[d]['ichimoku'].senkou_span_a[0] and d[0] < \
                        self.inds[d]['ichimoku'].senkou_span_b[0]:
                    stop_price = d[0] + self.inds[d]['stdev'] * self.std_scale
                    take_profit_price = d[0] - 2 * self.inds[d]['stdev'] * self.std_scale

                    qty = position_size(cash, stop_price, d[0], self.params.risk)
                    # qty = 100

                    self.o[d] = self.sell_bracket(data=d, limitprice=take_profit_price, stopprice=stop_price,
                                                  exectype=bt.Order.Market, size=qty)

                    self.o_refs[d._name] = [o.ref for o in self.o[d]]
                    self.log(f'CURRENCY {d._name}')
                    self.log(f'CURRENT CASH = {cash:.2f}')
                    self.log('SELL CREATE, %.2f' % d[0])
                    self.log(f'SELL QUANTITY = {qty}')
                    self.log(f'SL PRICE = {stop_price}')
                    self.log(f'TP PRICE = {take_profit_price}')
                    self.log(f'CURRENT PRICE = {d[0]}')

    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        dt1 = self.datas[0].datetime.time(0)

        # print('%s, %s' % (dt.isoformat(), txt))
        print('%s,%s, %s' % (dt.isoformat(), dt1.isoformat(), txt))

    def notify_trade(self, trade):
        dt = self.data.datetime.date()
        if trade.isclosed:
            print('{} {} Closed: Close Price: {}, PnL Gross {}, Net {}'.format(
                dt,
                trade.price,
                trade.data._name,
                round(trade.pnl, 2),
                round(trade.pnlcomm, 2)))

    def notify_order(self, order):
        print('{}: Order ref: {} / Type {} / Status {}'.format(
            self.data.datetime.date(0),
            order.ref, 'Buy' * order.isbuy() or 'Sell',
            order.getstatusname()))
        if 'Rejected' in order.getstatusname():
            print('Rejected')

        if order.status == order.Completed:
            print('order completed')

        if not order.alive():
            for i, d in enumerate(self.datas):
                if order.ref in self.o_refs[d._name]:
                    self.o_refs[d._name].remove(order.ref)
