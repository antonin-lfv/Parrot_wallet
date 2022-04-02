import json
from flask import Flask, request, redirect, abort, render_template, session, flash
from flask_caching import Cache
from main_module.static.utils import *

app = Flask(__name__)
app.config.from_object('config')
cache = Cache(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    cache.clear()
    session['available_crypto'] = AVAILABLE_CRYPTO
    session['changement'] = False
    return render_template('home.html')

@app.route('/trade', methods=['GET', 'POST'])
@cache.cached(timeout=200)
def trade():
    update_current_crypto_prices()
    with open('main_module/current_crypto_prices.json', 'r+') as crypto_prices:
        data = json.load(crypto_prices)
        crypto_diff = {}
        for crypto in AVAILABLE_CRYPTO:
            crypto_diff[crypto] = {'Prix': f"{round(data['TODAY']['Price'][crypto], 6):,}", 'Variation 24h': f"{round(data['TODAY']['Price'][crypto]-data['YESTERDAY']['Price'][crypto], 6):,}", 'Volume 24h': f"{round(data['TODAY']['Volume'][crypto]-data['YESTERDAY']['Price'][crypto], 3):,}"}
    return render_template('trade.html', crypto_diff=crypto_diff)

@app.route('/detailed_crypto/<string:crypto>', methods=['GET', 'POST'])
@cache.cached(timeout=200)
def detailed_crypto(crypto):
    df = get_crypto_price(symbol=crypto, start_date='2021-01-01', fulldf=True)
    fig = plot_exchange(df)
    fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('detailed_crypto.html', fig=fig, crypto=crypto, last_price=f"{round(df['Open'].iloc[-1], 6):,}", price_difference=f"{round(df['Open'].iloc[-1]-df['Open'].iloc[-2], 6):,}")

@app.route('/wallet', methods=['GET', 'POST'])
@cache.cached(timeout=200)
def wallet():
    update_current_crypto_prices()
    with open('main_module/wallet.json', 'r+') as my_wallet:
        data = json.load(my_wallet)
        if session['changement'] or data['Date'] != today.strftime('%Y-%m-%d'):
            """Update wallet"""
            data['main_solde_btc'], data['main_solde_dollars'] = 0, 0
            data['Date'] = today.strftime('%Y-%m-%d')
            # Restart wallet if necessary
            # restart_wallet()
            for k in AVAILABLE_CRYPTO:
                data['main_solde_btc'] += float(crypto_to_crypto(k, data[k], 'BTC-USD'))
                data['main_solde_dollars'] += float(crypto_to_dollars(k, data[k]))
            # Update json
            json.dump(data, open("main_module/wallet.json", "w"), indent=4)
            data['main_solde_btc'], data['main_solde_dollars'] = "{:.8f}".format(data['main_solde_btc']), f'{float("{:.2f}".format(data["main_solde_dollars"])):,}'
            session['changement'] = False

    return render_template('wallet.html', crypto_to_crypto=crypto_to_crypto, crypto_to_dollars=crypto_to_dollars, to_string=to_string, float=float, wallet=data)