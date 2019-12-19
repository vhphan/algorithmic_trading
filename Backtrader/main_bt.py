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

from helpers import print_trade_analysis, print_dict, print_sharpe_ratio, print_sqn, save_trade_analysis, save_plots
from oanda.oanda_data import get_historical_data_factory
import engulfing


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


def run_strategy(strategy, instruments=["AUD_USD"]):
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
        "from": "2018-01-01T00:00:00Z",
        "granularity": "H4",
        "to": "2019-01-01T00:00:00Z"
    }

    # crypto compare BTC USD
    # from_date = cc.to_seconds_epoch(datetime.datetime(2016, 1, 1))
    # to_date = cc.to_seconds_epoch(datetime.datetime(2018, 1, 1))
    # df = cc.get_df(from_date, to_date, time_period='histoday', coin='ETH', data_folder='data')

    # df = pd.read_pickle(r"C:\Users\vhphan\PycharmProjects\packt\Learn Algorithmic Trading\Chapter5\GOOG_data.pkl")
    # df = pd.read_csv('data/data_USD_JPY_20191118172246.csv', parse_dates=True, index_col='datetime')
    # df = df.loc['2014-01-01':'2017-01-01']

    # Pass it to the backtrader datafeed and add it to the cerebro

    # 4 hours

    data = []
    for i, instrument in enumerate(instruments):
        df = get_historical_data_factory(instrument, params)
        data.append(bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, compression=240))
        cerebro.adddata(data[i], name=instrument)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    cerebro.broker.set_shortcash(False)
    # Add a strategy
    cerebro.addstrategy(strategy)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001, leverage=1000_000)

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
        # save_trade_analysis(first_strategy.analyzers.ta.get_analysis(), instrument,
        #                     f'output/analysis_{strategy.__name__}.csv')
        print_sharpe_ratio(first_strategy.analyzers.sharpe.get_analysis())
        print_sqn(first_strategy.analyzers.sqn.get_analysis())
        print_dict(first_strategy.analyzers.draw_down.get_analysis())
    except Exception as e:
        print(e)

    # Get final portfolio Value
    portfolio_value = cerebro.broker.getvalue()

    # Print out the final result
    print(f'Final Portfolio Value: ${portfolio_value:.2f}')
    # print('Final Portfolio Value: ${0:.2f}'.format(portvalue))

    # plt.style.use('seaborn-notebook')
    plt.style.use('tableau-colorblind10')
    plt.rc('grid', color='k', linestyle='-', alpha=0.1)
    plt.rc('legend', loc='best')
    # bo = Bokeh()
    # bo.plot_result(strategies)

    plot_args = dict(style='candlestick',
                     # legendindloc='best',
                     # legendloc='upper right',
                     # legendloc='upper right',
                     legenddataloc='upper right',
                     grid=True,
                     #  Format string for the display of ticks on the x axis
                     fmt_x_ticks='%Y-%b-%d %H:%M',
                     # Format string for the display of data points values
                     fmt_x_data='%Y-%b-%d %H:%M',
                     subplot=True,
                     dpi=900,
                     numfigs=1,
                     # plotymargin=10.0,
                     iplot=False)

    # save_plots(figs, instrument, strategy, timestamp)

    #  separate plot by data feed. (if there is more than one)
    if len(first_strategy.datas) > 1:
        for i in range(len(first_strategy.datas)):
            for j, d in enumerate(first_strategy.datas):
                d.plotinfo.plot = i == j  # only one data feed to be plot. others = False
                # first_strategy.observers.buysell[j].plotinfo.plot = i == j

            cerebro.plot(**plot_args)


if __name__ == '__main__':
    # get_instruments()
    # run_strategy(strategies.StarsStrategy)
    # run_strategy(strat_singles.MeanReversionAPO)
    # run_strategy(strategies.MomentumStrategy1)
    # instruments = ['EUR_USD', 'GBP_USD', 'AUD_USD', 'NZD_USD', 'XAU_USD', 'XAG_USD']
    instruments = ['EUR_USD', 'GBP_USD']
    run_strategy(engulfing.Engulfing, instruments)
