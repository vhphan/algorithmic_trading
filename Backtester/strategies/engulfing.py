from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime
import backtrader as bt
from helpers import position_size

from generic import GenericStrategy


class Engulfing(GenericStrategy):

    def __init__(self):
        super(Engulfing, self).__init__()
        # using ta-lib instead
        # self.ema_s = bt.talib.EMA(self.data, timeperiod=self.params.window_s)
        # self.ema_m = bt.talib.EMA(self.data, timeperiod=self.params.window_m)
        # self.ema_l = bt.talib.EMA(self.data, timeperiod=self.params.window_l)
        self.ichimoku = bt.indicators.Ichimoku()
        # self.boll = bt.indicators.BollingerBands(period=self.p.window_s, devfactor=self.p.devfactor)
        self.std_dev = bt.indicators.StandardDeviation(period=self.p.window_s)
        self.engulfing = bt.talib.CDLENGULFING(self.dataopen, self.datahigh, self.datalow, self.dataclose)
        # self.bull_cross = bt.ind.CrossOver(self.ema_m, self.ema_l)

        # self.ema_s.csv = True
        # self.ema_m.csv = True
        # self.ema_l.csv = True
        self.engulfing.csv = True
        # self.boll.csv = True
        self.ichimoku.csv = True

        self.engulfing.plotinfo.subplot = True
        self.ichimoku.plotinfo.subplot = False
        self.ichimoku.plotinfo.plotlinelabels = False

        # self.ema_s.plotinfo.plot = False
        # self.ema_m.plotinfo.plot = False
        # self.ema_l.plotinfo.plot = False
        self.ichimoku.plot = True
        # self.boll.plotinfo.plot = False
        self.std_dev.plotinfo.plot = False
        # self.bull_cross.plotinfo.plot = False

    def next(self):

        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        self.log(
            f'Open, {self.dataopen[0]:.4f}, High, {self.datahigh[0]:.4f}, Low, {self.datalow[0]:.4f}, Close, {self.dataclose[0]:.4f}')

        cash = self.broker.get_cash()
        # Check if an order is pending ... if yes, we cannot send a 2nd one

        # if (self.sell_order_tp or self.sell_order_sl or self.buy_order) or (
        # self.buy_order_tp or self.buy_order_sl or self.sell_order):
        if self.order_refs:
            return
        else:
            print('no order refs')

        # Check if we are in the market
        # if len(self.data == 86):
        #     print('debug')

        if not self.position:

            # if self.engulfing == 100 and self.data[0] > self.ichimoku.senkou_span_a[0] and self.data[0] > \
            #         self.ichimoku.senkou_span_b[0]:
            #     entry_price = self.data.low[0]
            #     stop_price = self.data.close[0] - self.std_dev[0] * self.std_scale
            #     take_profit_price = self.data.close[0] + 2 * self.std_dev[0] * self.std_scale
            #
            #     qty = position_size(cash, stop_price, entry_price, self.params.risk)
            #
            #     # self.buy_order = self.buy_bracket(limitprice=take_profit_price, stopprice=stop_price,
            #     #                                   exectype=bt.Order.Market, size=qty)
            #
            #     valid_entry = self.data.datetime.datetime(60)
            #     valid_limit = valid_stop = datetime.timedelta(1000000)
            #     self.buy_order = self.buy_bracket(limitprice=take_profit_price, limitargs=dict(valid=valid_limit),
            #                                       stopprice=stop_price, stopargs=dict(valid=valid_stop),
            #                                       exectype=bt.Order.Limit, size=qty, price=entry_price,
            #                                       valid=valid_entry)
            #
            #     self.order_refs = [o.ref for o in self.buy_order]
            #
            #     self.log('BUY CREATE, %.2f' % self.dataclose[0])
            #     self.log(f'BUY QUANTITY = {qty}')
            #     self.log(f'ENTRY PRICE = {entry_price}')
            #     self.log(f'SL PRICE = {stop_price}')
            #     self.log(f'TP PRICE = {take_profit_price}')
            #     self.log(f'CURRENT PRICE = {self.data[0]}')

            if self.engulfing == -100 and self.data[0] < self.ichimoku.senkou_span_a[0] and self.data[0] < \
                    self.ichimoku.senkou_span_b[0]:

                entry_price = self.data.high[0]
                stop_price = entry_price + self.std_dev[0] * self.std_scale
                take_profit_price = entry_price - 2 * self.std_dev[0] * self.std_scale

                qty = position_size(cash, stop_price, entry_price, self.params.risk)

                # self.sell_order = self.sell_bracket(limitprice=take_profit_price, stopprice=stop_price,
                #                                     exectype=bt.Order.Market, size=qty)

                valid_entry = self.data.datetime.datetime(60)
                valid_limit = valid_stop = datetime.timedelta(1000000)
                self.sell_order = self.sell_bracket(limitprice=take_profit_price, limitargs=dict(valid=valid_limit),
                                                    stopprice=stop_price, stopargs=dict(valid=valid_stop),
                                                    exectype=bt.Order.Limit, size=qty, price=entry_price,
                                                    valid=valid_entry)

                self.order_refs = [o.ref for o in self.sell_order]

                self.log('SHORT SELL CREATE, %.2f' % self.dataclose[0])
                self.log(f'SELL QUANTITY = {qty}')
                self.log(f'ENTRY PRICE = {entry_price}')
                self.log(f'SL PRICE = {stop_price}')
                self.log(f'TP PRICE = {take_profit_price}')
                self.log(f'CURRENT PRICE = {self.data[0]}')

