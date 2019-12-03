"""
Single Instrument + Single Strategy
strategy are imported from strat_singles.py
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import random

import backtrader as bt
import matplotlib.pyplot as plt

import strat_singles
from helpers import print_trade_analysis, print_dict, print_sharpe_ratio, print_sqn
from oanda_data import get_historical_data_factory


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


def run_strategy(strategy):
    session_id = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    timestamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')

    # parse arguments
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro()
    cerebro.addwriter(bt.WriterFile, out=f'output/test_{timestamp}.csv', csv=True, rounding=2)

    # oanda method 1
    # params = {
    #     "from": "2018-01-01T00:00:00Z",
    #     "granularity": "H4",
    #     "includeFirst": True,
    #     "count": 5000,
    # }
    # df = get_historical_data(instrument, params)

    # oanda method 2 (instrument factory)
    params = {
        "from": "2016-01-01T00:00:00Z",
        "granularity": "H4",
        "to": "2018-01-01T00:00:00Z"
    }
    instrument = "EUR_USD"
    df = get_historical_data_factory(instrument, params)

    # df = pd.read_pickle(r"C:\Users\vhphan\PycharmProjects\packt\Learn Algorithmic Trading\Chapter5\GOOG_data.pkl")

    # df = pd.read_csv('data/data_USD_JPY_20191118172246.csv', parse_dates=True, index_col='datetime')

    # df = df.loc['2014-01-01':'2017-01-01']
    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, compression=240)
    # data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Days, compression=1)

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
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="draw_down")

    # Run over everything
    strategies = cerebro.run()
    first_strategy = strategies[0]

    # print the analyzers
    try:
        print_trade_analysis(first_strategy.analyzers.ta.get_analysis())
        print_sharpe_ratio(first_strategy.analyzers.sharpe.get_analysis())
        print_sqn(first_strategy.analyzers.sqn.get_analysis())
        print_dict(first_strategy.analyzers.draw_down.get_analysis())
    except Exception as e:
        print(e)
    # Get final portfolio Value
    portvalue = cerebro.broker.getvalue()

    # Print out the final result
    print(f'Final Portfolio Value: ${portvalue:.2f}')
    # print('Final Portfolio Value: ${0:.2f}'.format(portvalue))

    plt.style.use('seaborn-darkgrid')
    result = cerebro.plot(style='candlestick',
                          legendindloc='upper right',
                          legendloc='upper right',
                          legenddataloc='upper right',
                          grid=False,
                          #  Format string for the display of ticks on the x axis
                          fmt_x_ticks='%Y-%b-%d %H:%M',
                          # Format string for the display of data points values
                          fmt_x_data='%Y-%b-%d %H:%M',
                          subplot=True,
                          dpi=900,
                          numfigs=1,
                          plotymargin=10.0,
                          )


if __name__ == '__main__':
    # get_instruments()
    # run_strategy(strategies.StarsStrategy)
    # run_strategy(strat_singles.MeanReversionAPO)
    # run_strategy(strategies.MomentumStrategy1)
    run_strategy(strat_singles.Engulfing)
