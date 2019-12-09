from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import argparse
import datetime

import backtrader as bt

from oanda.oanda_data import get_historical_data_factory


class TestSizer(bt.Sizer):
    params = dict(stake=1)

    def _getsizing(self, comminfo, cash, data, isbuy):
        dt, i = self.strategy.datetime.date(), data._id
        s = self.p.stake * (1 + (not isbuy))
        print('{} Data {} OType {} Sizing to {}'.format(
            dt, data._name, ('buy' * isbuy) or 'sell', s))

        return s


class St(bt.Strategy):
    params = dict(
        enter=[1, 3, 4],  # data ids are 1 based
        hold=[7, 10, 15],  # data ids are 1 based
        usebracket=True,
        rawbracket=True,
        pentry=0.015,
        plimits=0.03,
        valid=10,
    )

    def notify_order(self, order):
        if order.status == order.Submitted:
            return

        dt, dn = self.datetime.date(), order.data._name
        print('{} {} Order {} Status {}'.format(
            dt, dn, order.ref, order.getstatusname())
        )

        whichord = ['main', 'stop', 'limit', 'close']
        if not order.alive():  # not alive - nullify
            dorders = self.o[order.data]
            idx = dorders.index(order)
            dorders[idx] = None
            print(idx)

            if all(x is None for x in dorders):
                dorders[:] = []  # empty list - New orders allowed

    def __init__(self):
        self.o = dict()  # orders per data (main, stop, limit, manual-close)
        self.holding = dict()  # holding periods per data

    def next(self):
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.date(), d._name
            pos = self.getposition(d).size
            print('{} {} Position {}'.format(dt, dn, pos))

            if not pos and not self.o.get(d, None):  # no market / no orders
                if dt.weekday() == self.p.enter[i]:
                    if not self.p.usebracket:
                        self.o[d] = [self.buy(data=d)]
                        print('{} {} Buy {}'.format(dt, dn, self.o[d][0].ref))

                    else:
                        p = d.close[0] * (1.0 - self.p.pentry)
                        pstp = p * (1.0 - self.p.plimits)
                        plmt = p * (1.0 + self.p.plimits)
                        valid = datetime.timedelta(self.p.valid)

                        if self.p.rawbracket:
                            o1 = self.buy(data=d, exectype=bt.Order.Limit,
                                          price=p, valid=valid, transmit=False)

                            o2 = self.sell(data=d, exectype=bt.Order.Stop,
                                           price=pstp, size=o1.size,
                                           transmit=False, parent=o1)

                            o3 = self.sell(data=d, exectype=bt.Order.Limit,
                                           price=plmt, size=o1.size,
                                           transmit=True, parent=o1)

                            self.o[d] = [o1, o2, o3]

                        else:
                            self.o[d] = self.buy_bracket(
                                data=d, price=p, stopprice=pstp,
                                limitprice=plmt, oargs=dict(valid=valid))

                        print('{} {} Main {} Stp {} Lmt {}'.format(
                            dt, dn, *(x.ref for x in self.o[d])))

                    self.holding[d] = 0

            elif pos:  # exiting can also happen after a number of days
                self.holding[d] += 1
                if self.holding[d] >= self.p.hold[i]:
                    o = self.close(data=d)
                    self.o[d].append(o)  # manual order to list of orders
                    print('{} {} Manual Close {}'.format(dt, dn, o.ref))
                    if self.p.usebracket:
                        self.cancel(self.o[d][1])  # cancel stop side
                        print('{} {} Cancel {}'.format(dt, dn, self.o[d][1]))


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed
    params = {
        "from": "2019-01-01T00:00:00Z",
        "granularity": "D",
        "to": "2019-07-01T00:00:00Z"
    }
    instruments = ['EUR_USD',
                   'USD_JPY',
                   'GBP_USD']

    for instrument in instruments:
        df = get_historical_data_factory(instrument, params)
        data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, compression=240)
        cerebro.adddata(data, name=instrument)

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')'))
    cerebro.broker.setcommission(commission=0.001)

    # Sizer
    # cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))
    cerebro.addsizer(TestSizer, **eval('dict(' + args.sizer + ')'))

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))

    # Execute
    cerebro.run()

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Multiple Values and Brackets'
        )
    )

    parser.add_argument('--data0', default='../../datas/nvda-1999-2014.txt',
                        required=False, help='Data0 to read in')

    parser.add_argument('--data1', default='../../datas/yhoo-1996-2014.txt',
                        required=False, help='Data1 to read in')

    parser.add_argument('--data2', default='../../datas/orcl-1995-2014.txt',
                        required=False, help='Data1 to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='2001-01-01',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='2007-01-01',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()