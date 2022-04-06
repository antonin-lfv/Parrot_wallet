import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly
import time
import numpy as np
import json
import requests
import pandas as pd
from datetime import datetime, timedelta, date
import yfinance as yf
from ta.trend import MACD
from ta.momentum import StochasticOscillator

today = datetime.today()
yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
two_days_ago = (today - timedelta(days=2)).strftime('%Y-%m-%d')

INCREASING_COLOR = '#30A03E'
DECREASING_COLOR = '#E94C1A'
MOVING_AVERAGE_COLOR = '#2BA1EE'
BOLLINGER_BANDS_COLOR = '#ccc'
AVAILABLE_CRYPTO = ['BUSD-USD', 'BTC-USD', 'ETH-USD', 'SOL-USD', 'VET-USD', 'MATIC-USD', 'BNB-USD', 'XRP-USD',
                    'DOGE-USD', 'SHIB-USD', 'LTC-USD', 'ATOM-USD', 'XLM-USD', 'GRT1-USD']


def restart_wallet():
    with open('main_module/wallet.json', 'r+') as my_wallet:
        data = json.load(my_wallet)
        for k in AVAILABLE_CRYPTO:
            data[k] = 0
        data['BUSD-USD'] = 100000
        data['main_solde_btc'] = crypto_to_crypto('BUSD-USD', 10000, 'BTC-USD')
        data['main_solde_dollars'] = crypto_to_dollars('BUSD-USD', 10000)
        data['Date'] = today.strftime('%Y-%m-%d')
        json.dump(data, open("main_module/wallet.json", "w"), indent=4)


def update_current_crypto_prices():
    # update from yahoo
    with open('main_module/current_crypto_prices.json', 'r+') as crypto_prices:
        data = json.load(crypto_prices)
        if data['TODAY']['Date'] != today.strftime('%Y-%m-%d'):
            for k in AVAILABLE_CRYPTO:
                df = get_crypto_price(k, start_date=two_days_ago, fulldf=True)
                data['YESTERDAY']['Price'][k] = float(df['Open'].iloc[-2])
                data['TODAY']['Price'][k] = float(df['Open'].iloc[-1])
                data['YESTERDAY']['Volume'][k] = float(df['Volume'].iloc[-2])
                data['TODAY']['Volume'][k] = float(df['Volume'].iloc[-1])
            data['TODAY']['Date'] = today.strftime('%Y-%m-%d')
            data['YESTERDAY']['Date'] = yesterday
        json.dump(data, open("main_module/current_crypto_prices.json", "w"), indent=4)


def get_crypto_price(symbol: str, fulldf: bool, start_date=None):
    if start_date == two_days_ago and not fulldf:
        # From json get last 2 prices and volumes
        with open('main_module/current_crypto_prices.json', 'r+') as crypto_prices:
            data = json.load(crypto_prices)
            df = [float(data['TODAY']['Price'][symbol]), float(data['YESTERDAY']['Price'][symbol]),
                  float(data['TODAY']['Volume'][symbol]), float(data['YESTERDAY']['Volume'][symbol])]
    else:
        # from yahoo
        df = yf.download(symbol, start=start_date)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['Date'] = df.index
        if start_date:
            df = df[df.index >= start_date]
    return df


def crypto_to_dollars(crypto: str, amount):
    crypto_price = get_crypto_price(symbol=crypto, start_date=two_days_ago, fulldf=False)[0]
    return "{:.8f}".format(crypto_price * amount)


def dollars_to_crypto(crypto: str, amount):
    crypto_price = get_crypto_price(symbol=crypto, start_date=two_days_ago, fulldf=False)[0]
    return "{:.8f}".format(amount / crypto_price)


def crypto_to_crypto(crypto1: str, amount_crypto1, crypto2: str):
    crypto_price_1 = get_crypto_price(symbol=crypto1, start_date=two_days_ago, fulldf=False)[0]
    crypto_price_2 = get_crypto_price(symbol=crypto2, start_date=two_days_ago, fulldf=False)[0]
    return "{:.8f}".format(amount_crypto1 * crypto_price_1 / crypto_price_2)


def convert_crypto(crypto1: str, crypto2: str, amount_crypto1=None, amount_crypto2=None):
    # Execute the transaction
    with open('main_module/wallet.json', 'r+') as my_wallet:
        wallet = json.load(my_wallet)
        if (amount_crypto1 and wallet[crypto1] >= amount_crypto1) or (
                amount_crypto2 and wallet[crypto1] >= float(crypto_to_crypto(crypto2, amount_crypto2, crypto1))):
            # Verify if there is enough in wallet
            if amount_crypto1 is not None:
                wallet[crypto1] -= float(amount_crypto1)
                wallet[crypto2] += float(crypto_to_crypto(crypto1, amount_crypto1, crypto2))
            elif amount_crypto2 is not None:
                wallet[crypto1] -= float(crypto_to_crypto(crypto2, amount_crypto2, crypto1))
                wallet[crypto2] += float(amount_crypto2)
            # Update main soldes
            wallet['main_solde_btc'], wallet['main_solde_dollars'] = 0, 0
            for k in AVAILABLE_CRYPTO:
                wallet['main_solde_btc'] += float(crypto_to_crypto(k, wallet[k], 'BTC-USD'))
                wallet['main_solde_dollars'] += float(crypto_to_dollars(k, wallet[k]))
            wallet['Date'] = today.strftime('%Y-%m-%d')
            json.dump(wallet, open("main_module/wallet.json", "w"), indent=4)


def to_string(significant_digits: int, number):
    return f'{float(("{:." + str(significant_digits) + "f}").format(number)):,}'


def plot_exchange(df):
    # MACD
    macd = MACD(close=df['Close'],
                window_slow=26,
                window_fast=12,
                window_sign=9)

    # stochastic
    stoch = StochasticOscillator(high=df['High'],
                                 close=df['Close'],
                                 low=df['Low'],
                                 window=14,
                                 smooth_window=3)

    # add subplot properties when initializing fig variable
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02,
                        row_heights=[0.5, 0.1, 0.2, 0.2])

    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'], name='market data'))

    fig.add_trace(go.Scatter(x=df.index,
                             y=df['MA5'],
                             opacity=0.7,
                             line=dict(color='blue', width=2),
                             name='MA 5'))

    fig.add_trace(go.Scatter(x=df.index,
                             y=df['MA20'],
                             opacity=0.7,
                             line=dict(color='orange', width=2),
                             name='MA 20'))

    # Plot volume trace on 2nd row
    colors = ['green' if row['Open'] - row['Close'] >= 0
              else 'red' for index, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index,
                         y=df['Volume'],
                         marker_color=colors
                         ), row=2, col=1)

    # Plot MACD trace on 3rd row
    colorsM = ['green' if val >= 0
               else 'red' for val in macd.macd_diff()]
    fig.add_trace(go.Bar(x=df.index,
                         y=macd.macd_diff(),
                         marker_color=colorsM
                         ), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index,
                             y=macd.macd(),
                             line=dict(color='black', width=2)
                             ), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index,
                             y=macd.macd_signal(),
                             line=dict(color='blue', width=1)
                             ), row=3, col=1)

    # Plot stochastics trace on 4th row
    fig.add_trace(go.Scatter(x=df.index,
                             y=stoch.stoch(),
                             line=dict(color='black', width=2)
                             ), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index,
                             y=stoch.stoch_signal(),
                             line=dict(color='blue', width=1)
                             ), row=4, col=1)

    # update layout by changing the plot size, hiding legends & rangeslider, and removing gaps between dates
    fig.update_layout(height=800,
                      showlegend=False,
                      xaxis_rangeslider_visible=False)

    # Make the title dynamic to reflect whichever stock we are analyzing
    fig.update_layout(
        yaxis_title='Stock Price',
    )

    # update y-axis label
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="MACD", showgrid=False, row=3, col=1)
    fig.update_yaxes(title_text="Stoch", row=4, col=1)

    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=15, label="15m", step="minute", stepmode="backward"),
                dict(count=45, label="45m", step="minute", stepmode="backward"),
                dict(count=1, label="HTD", step="hour", stepmode="todate"),
                dict(count=3, label="3h", step="hour", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    return fig
