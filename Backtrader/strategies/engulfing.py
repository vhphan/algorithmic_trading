from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime
import backtrader as bt
from generic import GenericStrategy


class Engulfing(GenericStrategy):

    def __init__(self):

        super(Engulfing, self).__init__()
        add_header = []
        for i, d in enumerate(self.datas):
            self.order_refs[d._name] = []
            self.indicators[d] = dict()
            self.indicators[d]['ichimoku'] = bt.indicators.Ichimoku()
            self.indicators[d]['engulfing'] = bt.talib.CDLENGULFING(d.open, d.high, d.low, d.close)
            self.indicators[d]['stdev'] = bt.indicators.StandardDeviation(period=self.p.window_s)

            self.indicators[d]['stdev'].plotinfo.subplot = False
            self.indicators[d]['ichimoku'].plotinfo.subplot = False
            self.indicators[d]['engulfing'].plotinfo.subplot = True

            self.indicators[d]['stdev'].plotinfo.plot = False
            self.indicators[d]['ichimoku'].plotinfo.plot = False
            self.indicators[d]['engulfing'].plotinfo.plot = True

            if i == 0:
                for key in self.indicators[d]:
                    add_header.append(key)

        self.setup_csv_file(add_header=add_header)

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

        for i, d in enumerate(self.datas):

            dt, dn = self.datetime.date(), d._name
            pos = self.getposition(d).size
            indicators = self.indicators[d]

            if pos > 0:
                print('{} {} Position {}'.format(dt, dn, pos))

            self.log(
                f'{dn} Open, {d.open[0]:.4f}, High, {d.high[0]:.4f}, Low, {d.low[0]:.4f}, Close, {d.close[0]:.4f}')

            with open(self.csv_file, 'a+') as f:
                df_log = f'{dt}, {d.open[0]}, {d.high[0]}, {d.low[0]}, {d.close[0]}, {d.volume[0]}'
                for key in indicators:
                    df_log += f', {round(indicators[key][0],5)}'

                f.write(df_log + '\n')

            cash = self.broker.get_cash()
            # Check if an order is pending ... if yes, we cannot send a 2nd one

            if self.order_refs[dn]:
                return
            # else:
            #     print(f'no order refs for {dn}')

            if not pos:
                self.run_strategy(d, dn, indicators)

    def run_strategy(self, d, dn, indicators):

        if indicators['engulfing'] == 100 and d[0] > indicators['ichimoku'].senkou_span_a[0] and d[0] > \
                indicators['ichimoku'].senkou_span_b[0]:
            entry_price = d.low[0]
            stop_price = d.close[0] - indicators['stdev'][0] * self.std_scale
            take_profit_price = d.close[0] + 2 * indicators['stdev'][0] * self.std_scale

            qty = self.size_position(price=entry_price, stop=stop_price, risk=self.params.risk)

            valid_entry = d.datetime.datetime(0) + datetime.timedelta(hours=self.valid_hours)
            valid_limit = valid_stop = datetime.timedelta(1_000_000)

            self.buy_order[dn] = self.buy_bracket(data=d, limitprice=take_profit_price,
                                                  limitargs=dict(valid=valid_limit),
                                                  stopprice=stop_price, stopargs=dict(valid=valid_stop),
                                                  exectype=bt.Order.Limit, size=qty, price=entry_price,
                                                  valid=valid_entry)

            self.order_refs[dn] = [o.ref for o in self.buy_order[dn]]

            self.log('BUY CREATE, %.2f' % d.close[0])
            self.log(f'BUY QUANTITY = {qty}')
            self.log(f'ENTRY PRICE = {entry_price}')
            self.log(f'SL PRICE = {stop_price}')
            self.log(f'TP PRICE = {take_profit_price}')
            self.log(f'CURRENT PRICE = {d[0]}')

        if indicators['engulfing'] == -100 and d[0] < indicators['ichimoku'].senkou_span_a[0] and d[0] < \
                indicators['ichimoku'].senkou_span_b[0]:
            entry_price = d.high[0]
            stop_price = entry_price + indicators['stdev'][0] * self.std_scale
            take_profit_price = entry_price - 2 * indicators['stdev'][0] * self.std_scale

            qty = self.size_position(price=entry_price, stop=stop_price, risk=self.params.risk)
            valid_entry = d.datetime.datetime(0) + datetime.timedelta(hours=self.valid_hours)
            valid_limit = valid_stop = datetime.timedelta(1000000)
            self.sell_order[dn] = self.sell_bracket(data=d, limitprice=take_profit_price,
                                                    limitargs=dict(valid=valid_limit),
                                                    stopprice=stop_price, stopargs=dict(valid=valid_stop),
                                                    exectype=bt.Order.Limit, size=qty, price=entry_price,
                                                    valid=valid_entry)

            self.order_refs[dn] = [o.ref for o in self.sell_order[dn]]

            self.log('SHORT SELL CREATE, %.2f' % d.close[0])
            self.log(f'SELL QUANTITY = {qty}')
            self.log(f'ENTRY PRICE = {entry_price}')
            self.log(f'SL PRICE = {stop_price}')
            self.log(f'TP PRICE = {take_profit_price}')
            self.log(f'CURRENT PRICE = {d[0]}')
