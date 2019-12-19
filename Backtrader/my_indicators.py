from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader.indicators import MovingAverageBase, ExponentialSmoothing, StandardDeviation, Average
import statistics


class SpecialEMA(Average):
    lines = ('special_ema',)
    params = dict(period=20)
    plotinfo = dict(subplot=False)
    plotlines = dict(special_ema=dict(ls='--'))

    def __init__(self):
        self.addminperiod(self.p.period)
        self.alpha = 2.0 / (1.0 + self.p.period)  # def EMA value
        self.alpha1 = 1.0 - self.alpha
        super(SpecialEMA, self).__init__()

    def next(self):
        stdev = statistics.stdev(self.data.get(size=self.p.period))
        self.lines.special_ema[0] = self.data[-1] * self.alpha1 + self.data[0] * self.alpha * stdev


class MorningStarCandle(bt.Indicator):
    lines = ('morning_star',)
    plotinfo = dict(
        # Add extra margins above and below the 1s and -1s
        plotymargin=0.15,

        # Plot a reference horizontal line at 1.0 and -1.0
        plothlines=[1.0, -1.0],

        # Simplify the y scale to 1.0 and -1.0
        plotyticks=[1.0, -1.0])

    # Plot the line "overunder" (the only one) with dash style
    # ls stands for linestyle and is directly passed to matplotlib
    plotlines = dict(overunder=dict(ls='--'))

    def __init__(self):
        self.addminperiod(3)

    def next(self):
        # 1st candle
        candles = dict.fromkeys(['open', 'high', 'low', 'close'], None)
        candles['open'] = self.data.open.get(size=3)
        candles['high'] = self.data.high.get(size=3)
        candles['low'] = self.data.low.get(size=3)
        candles['close'] = self.data.close.get(size=3)

        if candles['close'][0] < candles['open'][0] and candles['close'][2] > candles['open'][
            2]:  # 1st bar red, 3rd bar green
            if min(candles['close'][0], candles['open'][0]) > max(candles['close'][1], candles['open'][1]) and \
                    min(candles['close'][2], candles['open'][2]) > max(candles['close'][1], candles['open'][1]):
                self.lines.morning_star[0] = 100
            else:
                self.lines.morning_star[0] = 0

        else:
            self.lines.morning_star[0] = 0
