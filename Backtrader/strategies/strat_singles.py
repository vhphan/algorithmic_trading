from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import backtrader as bt
from helpers import my_position_size, my_std_scale
from my_indicators import SpecialEMA

from generic import GenericStrategy


class MomentumStrategy1(GenericStrategy):

    def __init__(self):
        super(MomentumStrategy1, self).__init__()

        # using ta-lib instead
        self.ema_s = bt.talib.EMA(self.data, timeperiod=self.params.window_s)
        self.ema_m = bt.talib.EMA(self.data, timeperiod=self.params.window_m)
        self.ema_l = bt.talib.EMA(self.data, timeperiod=self.params.window_l)
        self.ichimoku = bt.indicators.Ichimoku()
        self.boll = bt.indicators.BollingerBands(period=self.p.window_s, devfactor=self.p.devfactor)
        self.std_dev = bt.indicators.StandardDeviation(period=self.p.window_s)
        self.engulfing = bt.talib.CDLENGULFING(self.dataopen, self.datahigh, self.datalow, self.dataclose)
        self.bull_cross = bt.ind.CrossOver(self.dataclose, self.ema_s)

        self.ema_s.csv = True
        self.ema_m.csv = True
        self.ema_l.csv = True
        self.engulfing.csv = True
        self.boll.csv = True
        self.ichimoku.csv = True

        self.engulfing.plotinfo.subplot = True
        self.ichimoku.plotinfo.subplot = False
        self.ichimoku.plotinfo.plotlinelabels = False

        self.ema_s.plotinfo.plot = True
        self.ema_m.plotinfo.plot = True
        self.ema_l.plotinfo.plot = True
        self.ichimoku.plotinfo.plot = False
        self.boll.plotinfo.plot = False
        self.std_dev.plotinfo.plot = False
        self.bull_cross.plotinfo.plot = True

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        cash = self.broker.get_cash()
        # Check if an order is pending ... if yes, we cannot send a 2nd one

        # if (self.sell_order_tp or self.sell_order_sl or self.buy_order) or (
        # self.buy_order_tp or self.buy_order_sl or self.sell_order):
        if self.order_refs:
            return
        else:
            print('order refs is false')

        # Check if we are in the market
        if not self.position:

            if self.ema_m > self.ema_l and self.bull_cross[-1] == 1 and self.dataclose > self.ema_s and \
                    self.dataclose > self.dataopen and self.dataclose[-1] > self.dataopen[-1]:
                stop_price = self.data.close[0] - self.std_dev[0] * self.std_scale
                take_profit_price = self.data.close[0] + 2 * self.std_dev[0] * self.std_scale

                qty = my_position_size(cash, stop_price, self.data.close[0], self.p.risk)

                self.buy_order = self.buy_bracket(limitprice=take_profit_price, stopprice=stop_price,
                                                  exectype=bt.Order.Market, size=qty)
                self.order_refs = [o.ref for o in self.buy_order]
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.log(f'BUY QUANTITY = {qty}')
                self.log('Engulf %.0f' % self.last_engulf)
                self.log(f'ema_s={self.ema_s[0]} ema_m={self.ema_m[0]}')

            # if self.ema_m < self.ema_l and self.bull_cross[-1] == -1 and self.dataclose < self.ema_s and \
            #         self.dataclose < self.dataopen and self.dataclose[-1] < self.dataopen[-1]:
            #     stop_price = self.data.close[0] + self.std_dev[0] * self.std_scale
            #     take_profit_price = self.data.close[0] - 2 * self.std_dev[0] * self.std_scale
            #
            #     qty = position_size(cash, stop_price, self.data.close[0], self.p.risk)
            # self.sell_order = self.sell_bracket(limitprice=take_profit_price, stopprice=stop_price,
            #                                     exectype=bt.Order.Market, size=qty)
            # self.order_refs = [o.ref for o in self.sell_order]

            # self.log('SHORT SELL CREATE, %.2f' % self.dataclose[0])
            # self.log(f'SELL QUANTITY = {qty}')
            # self.log('Engulf %.0f' % self.last_engulf)
            # self.log(f'ema_s={self.ema_s[0]} ema_m={self.ema_m[0]}')

        else:
            pass


class StarsStrategy(GenericStrategy):

    def __init__(self):
        super(StarsStrategy, self).__init__()

        self.ema_s = bt.talib.EMA(self.data, timeperiod=self.params.window_s)
        self.ema_m = bt.talib.EMA(self.data, timeperiod=self.params.window_m)
        self.ema_l = bt.talib.EMA(self.data, timeperiod=self.params.window_l)
        self.ichimoku = bt.indicators.Ichimoku()
        self.boll = bt.indicators.BollingerBands(period=self.p.window_s, devfactor=self.p.devfactor)
        self.std_dev = bt.indicators.StandardDeviation(period=self.p.window_s)

        self.engulfing = bt.talib.CDLENGULFING(self.data.open, self.data.high, self.data.low, self.data.close)
        self.evening_star = bt.talib.CDLEVENINGSTAR(self.data.open, self.data.high, self.data.low, self.data.close)
        self.shooting_star = bt.talib.CDLSHOOTINGSTAR(self.data.open, self.data.high, self.data.low, self.data.close)
        self.hammer = bt.talib.CDLHAMMER(self.data.open, self.data.high, self.data.low, self.data.close)
        self.morning_star = bt.talib.CDLMORNINGSTAR(self.data.open, self.data.high, self.data.low, self.data.close)
        # self.morning_star = MorningStarCandle()

        self.bull_cross = bt.ind.CrossOver(self.ema_m, self.ema_l)

        self.ema_s.csv = True
        self.ema_m.csv = True
        self.ema_l.csv = True
        self.engulfing.csv = True
        self.boll.csv = True
        self.ichimoku.csv = True
        self.evening_star.csv = True
        self.shooting_star.csv = True
        self.morning_star.csv = True
        self.hammer.csv = True

        # sub plots
        # self.engulfing.plotinfo.subplot = False
        self.ichimoku.plotinfo.subplot = False

        self.evening_star.plotinfo.subplot = True
        self.morning_star.plotinfo.subplot = True
        self.shooting_star.plotinfo.subplot = True
        self.hammer.plotinfo.subplot = True

        self.evening_star.plotinfo.plotymargin = 1.0
        self.morning_star.plotinfo.plotymargin = 1.0
        self.shooting_star.plotinfo.plotymargin = 1.0
        self.hammer.plotinfo.plotymargin = 1.0
        # self.hammer.plotinfo._candleplot.markersize =1.0

        self.evening_star.plotlines._candleplot.markersize = '2.0'
        self.morning_star.plotlines._candleplot.markersize = '2.0'
        self.shooting_star.plotlines._candleplot.markersize = '2.0'
        self.hammer.plotlines._candleplot.markersize = '2.0'

        # labels legend
        self.ichimoku.plotinfo.plotlinelabels = False

        # hide plots
        self.ema_s.plotinfo.plot = False
        self.ema_m.plotinfo.plot = False
        self.ema_l.plotinfo.plot = False

        self.engulfing.plotinfo.plot = False
        self.evening_star.plotinfo.plot = False
        self.boll.plotinfo.plot = False
        self.std_dev.plotinfo.plot = False
        self.bull_cross.plotinfo.plot = False

        self.morning_star.plotinfo.plot = True
        self.ichimoku.plotinfo.plot = True
        self.shooting_star.plotinfo.plot = True
        self.hammer.plotinfo.plot = True

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        cash = self.broker.get_cash()
        # Check if an order is pending ... if yes, we cannot send a 2nd one

        # if (self.sell_order_tp or self.sell_order_sl or self.buy_order) or (
        # self.buy_order_tp or self.buy_order_sl or self.sell_order):
        if self.order_refs:
            return
        else:
            print('pass')

        # Check if we are in the market
        if not self.position:

            if (self.hammer == 100 or self.morning_star == 100) and self.data[0] > self.ichimoku.senkou_span_a[0] \
                    and self.data[0] > self.ichimoku.senkou_span_b[0]:
                stop_price = self.data.close[0] - self.std_dev[0] * self.std_scale
                take_profit_price = self.data.close[0] + 2 * self.std_dev[0] * self.std_scale
                qty = my_position_size(cash, stop_price, self.data.close[0], self.p.risk)

                self.buy_order = self.buy_bracket(limitprice=take_profit_price, stopprice=stop_price,
                                                  exectype=bt.Order.Market, size=qty)
                self.order_refs = [o.ref for o in self.buy_order]

                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.log(f'BUY QUANTITY = {qty}')
                self.log('Engulf %.0f' % self.last_engulf)
                self.log(f'ema_s={self.ema_s[0]} ema_m={self.ema_m[0]}')

            if (self.shooting_star == -100 or self.evening_star == -100) and self.data[0] < self.ichimoku.senkou_span_a[
                0] and self.data[0] < \
                    self.ichimoku.senkou_span_b[0]:
                stop_price = self.data.close[0] + self.std_dev[0] * self.std_scale
                take_profit_price = self.data.close[0] - 2 * self.std_dev[0] * self.std_scale

                qty = my_position_size(cash, stop_price, self.data.close[0], self.p.risk)

                # self.sell_order = self.sell_bracket(limitprice=take_profit_price, stopprice=stop_price,
                #                                     exectype=bt.Order.Market, size=qty)
                # self.order_refs = [o.ref for o in self.sell_order]

                self.log('SHORT SELL CREATE, %.2f' % self.dataclose[0])
                self.log(f'SELL QUANTITY = {qty}')
                self.log('Engulf %.0f' % self.last_engulf)
                self.log(f'ema_s={self.ema_s[0]} ema_m={self.ema_m[0]}')

        else:
            pass


class MeanReversionAPO(GenericStrategy):

    def __init__(self):
        super(MeanReversionAPO, self).__init__()

        self.order = None
        self.last_sell_price = 0
        self.last_buy_price = 0
        self.params.window_s = 10
        self.params.window_m = 40

        self.ppo = bt.talib.PPO(self.data, slowperiod=self.params.window_m, fastperiod=self.params.window_s, matype=1)
        self.std_dev = bt.indicators.StandardDeviation(period=self.p.window_s)

        self.special_ema_m = SpecialEMA(period=self.p.window_m)
        self.ema_m = bt.indicators.ExponentialMovingAverage(period=self.p.window_m)

        # Constants that define strategy behavior/thresholds
        self.PPO_VALUE_FOR_BUY_ENTRY = -0.1  # APO trading signal value below which to enter buy-orders/long-position
        self.PPO_VALUE_FOR_SELL_ENTRY = 0.1  # APO trading signal value above which to enter sell-orders/short-position
        self.MIN_PRICE_MOVE_FROM_LAST_TRADE_RATIO = 0.05  # Minimum price change since last trade before considering trading
        # again,
        # this is to prevent over-trading at/around same prices
        self.NUM_SHARES_PER_TRADE = 10  # Number of shares to buy/sell on every trade
        self.MIN_PROFIT_TO_CLOSE = 10 * self.NUM_SHARES_PER_TRADE  # Minimum Open/Unrealized profit at which to close
        # positions and
        # lock profits

        # self.ema_s = bt.talib.EMA(self.data, timeperiod=self.params.window_s)
        # self.ema_m = bt.talib.EMA(self.data, timeperiod=self.params.window_m)

        # self.ema_s.csv = True
        # self.ema_m.csv = True

        # sub plots
        # self.engulfing.plotinfo.subplot = False
        # self.hammer.plotinfo._candleplot.markersize =1.0

        # labels legend
        # self.ichimoku.plotinfo.plotlinelabels = False

        # hide plots
        # self.ema_s.plotinfo.plot = False
        # self.ema_m.plotinfo.plot = False

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
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def next(self):

        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        cash = self.broker.get_cash()

        pos = self.getposition(self.data)  # for the default data (aka self.data0 and aka self.datas[0])
        comm_info = self.broker.getcommissioninfo(self.data)
        open_pnl = comm_info.profitandloss(pos.size, pos.price, self.data.close[0])
        print('open pnl', open_pnl)

        if self.last_sell_price == 0:
            self.last_sell_price = 0.000001
        if self.last_buy_price == 0:
            self.last_buy_price = 0.000001

        if ((self.ppo > self.PPO_VALUE_FOR_SELL_ENTRY and
             abs(self.data.close[
                     0] - self.last_sell_price) / self.last_sell_price > self.MIN_PRICE_MOVE_FROM_LAST_TRADE_RATIO)
                or (pos.size >= 0 and (self.ppo >= 0 or open_pnl > self.MIN_PROFIT_TO_CLOSE))):
            self.last_sell_price = self.data.close[0]
            self.sell_order = self.sell(size=self.NUM_SHARES_PER_TRADE)
            self.order = self.sell_order
            self.log('SHORT SELL CREATE, %.2f' % self.dataclose[0])
            self.log(f'SELL QUANTITY = {self.NUM_SHARES_PER_TRADE}')

        elif ((self.ppo < self.PPO_VALUE_FOR_SELL_ENTRY and
               abs(self.data.close[
                       0] - self.last_buy_price) / self.last_buy_price > self.MIN_PRICE_MOVE_FROM_LAST_TRADE_RATIO)
              or (pos.size <= 0 and (self.ppo <= 0 or open_pnl > self.MIN_PROFIT_TO_CLOSE))):
            self.last_buy_price = self.data.close[0]
            self.buy_order = self.buy(size=self.NUM_SHARES_PER_TRADE)
            self.order = self.buy_order
            self.log('LONG BUY CREATE, %.2f' % self.dataclose[0])
            self.log(f'BUY QUANTITY = {self.NUM_SHARES_PER_TRADE}')
