from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime
import backtrader as bt
from helpers import my_position_size

from generic import GenericStrategy


class StatsArb(GenericStrategy):

    def __init__(self):

        super(StatsArb, self).__init__()
        self.params.window_s = 20
        self.params.window_l = 200
        self.value_buy_entry = 0.01
        self.value_sell_entry = -0.01
        self.min_price_movement_from_last_trade = 0.01

        # self.boll.csv = True

        # self.ichimoku.plotinfo.plotlinelabels = False

        # self.ema_s.plotinfo.plot = False

        current_time_frame = bt.TimeFrame.Names[self.data._timeframe]
        valid_candles = 10
        if current_time_frame == 'Days':
            multiplier = 24 / self.data._compression
        elif current_time_frame == 'Minutes':
            multiplier = self.data._compression / 60
        else:
            multiplier = 10

        self.valid_hours = valid_candles * multiplier

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

            if self.engulfing == 100 and self.data[0] > self.ichimoku.senkou_span_a[0] and self.data[0] > \
                    self.ichimoku.senkou_span_b[0]:
                entry_price = self.data.low[0]
                stop_price = self.data.close[0] - self.std_dev[0] * self.std_scale
                take_profit_price = self.data.close[0] + 2 * self.std_dev[0] * self.std_scale

                # qty = my_position_size(cash, stop_price, entry_price, self.params.risk)
                qty = self.size_position(price=entry_price, stop=stop_price, risk=self.params.risk)
                # self.buy_order = self.buy_bracket(limitprice=take_profit_price, stopprice=stop_price,
                #                                   exectype=bt.Order.Market, size=qty)

                # valid_entry = self.data.datetime.datetime(60)

                valid_entry = self.data.datetime.datetime(0) + datetime.timedelta(hours=self.valid_hours)
                valid_limit = valid_stop = datetime.timedelta(1_000_000)

                self.buy_order = self.buy_bracket(limitprice=take_profit_price, limitargs=dict(valid=valid_limit),
                                                  stopprice=stop_price, stopargs=dict(valid=valid_stop),
                                                  exectype=bt.Order.Limit, size=qty, price=entry_price,
                                                  valid=valid_entry)

                self.order_refs = [o.ref for o in self.buy_order]

                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.log(f'BUY QUANTITY = {qty}')
                self.log(f'ENTRY PRICE = {entry_price}')
                self.log(f'SL PRICE = {stop_price}')
                self.log(f'TP PRICE = {take_profit_price}')
                self.log(f'CURRENT PRICE = {self.data[0]}')

            if self.engulfing == -100 and self.data[0] < self.ichimoku.senkou_span_a[0] and self.data[0] < self.ichimoku.senkou_span_b[0]:
                entry_price = self.data.high[0]
                stop_price = entry_price + self.std_dev[0] * self.std_scale
                take_profit_price = entry_price - 2 * self.std_dev[0] * self.std_scale

                # qty = my_position_size(cash, stop_price, entry_price, self.params.risk)
                qty = self.size_position(price=entry_price, stop=stop_price, risk=self.params.risk)

                # self.sell_order = self.sell_bracket(limitprice=take_profit_price, stopprice=stop_price,
                #                                     exectype=bt.Order.Market, size=qty)

                # valid_entry = self.data.datetime.datetime(60)
                valid_entry = self.data.datetime.datetime(0) + datetime.timedelta(hours=self.valid_hours)

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
