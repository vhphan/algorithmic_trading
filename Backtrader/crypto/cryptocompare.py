import requests
import json
import pandas as pd
import datetime
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from keys import cryptocompare_api_key as api_key


def draw_corr_map(corr):
    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(11, 9))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1, center=0,
                square=True, linewidths=.5, annot=True, cbar_kws={"shrink": .5}, annot_kws={"size": 15})
    plt.show()


def to_seconds_epoch(dt):
    """
    Covert datetime to number of seconds since epoch
    :param dt: datetime object
    :return: seconds since 1970-01-01
    """
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds()


def to_datetime(seconds):
    """
    Convert number of seconds since epoch to a datetimeobject
    :param seconds: number of seconds since epoch
    :return: datetime object
    """
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=seconds)


def get_data(date, time_period='histoday', coin='BTC', agg=None):
    """ Query the API for 2000 days historical price data starting from "date". """
    url = f"https://min-api.cryptocompare.com/data/{time_period}?fsym={coin}&tsym=USD&limit=2000&toTs={date}&api_key={api_key}"
    if agg is not None:
        url = url + f'&aggregate={agg}'
    r = requests.get(url)
    ipdata = r.json()
    return ipdata


def get_df(from_date, to_date, time_period='histoday', coin='BTC', agg=None, data_folder='data'):
    """ Get historical price data between two dates. """
    if agg is not None:
        file = f'{data_folder}/{coin}_{time_period}_{from_date}_{to_date}_{agg}.csv'
    else:
        file = f'{data_folder}/{coin}_{time_period}_{from_date}_{to_date}.csv'

    try:
        df = pd.read_csv(file)
        df = df.rename(columns={'time': 'datetime', 'volumeto': 'volume'})

        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)

    except FileNotFoundError:
        date = to_date
        holder = []
        # While the earliest date returned is later than the earliest date requested, keep on querying the API
        # and adding the results to a list.
        while date > from_date:
            data = get_data(date, time_period, coin, agg)
            holder.append(pd.DataFrame(data['Data']))
            date = data['TimeFrom']
        # Join together all of the API queries in the list.
        df = pd.concat(holder, axis=0)
        # Remove data points from before from_date
        df = df[df['time'] > from_date]
        # Convert to timestamp to readable date format
        df['time'] = pd.to_datetime(df['time'], unit='s')

        # rename columns for backtrader
        df = df.rename(columns={'time': 'datetime', 'volumeto': 'volume'})

        # Make the DataFrame index the time
        df.set_index('datetime', inplace=True)
        # And sort it so its in time order
        df.sort_index(ascending=True, inplace=True)
        df.to_csv(file, index=True)

    return df[['open', 'high', 'low', 'close', 'volume']]


if __name__ == '__main__':

    coins = ['BTC', 'ETH', 'DOGE', 'USDT', 'DASH']
    holder = []
    from_date = to_seconds_epoch(datetime.datetime(2018, 9, 1))
    to_date = to_seconds_epoch(datetime.datetime(2019, 9, 1))
    time_period = 'histohour'
    agg = 8

    for coin in coins:
        holder.append(get_df(from_date, to_date, time_period, coin, agg, data_folder='../data'))

    df = pd.concat(holder, axis=1)
    df = df.divide(df.shift()) - 1  # Get rate of return

    correlations = df.corr()  # Get correlation matrix
    corr_close = correlations['close'].loc['close']

    corr_close.index = coins
    corr_close.columns = coins
    draw_corr_map(corr_close)
