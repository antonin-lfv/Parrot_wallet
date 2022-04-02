from static.utils import *

if __name__ == '__main__':
    # BTC, ETH, SOL, VET, MATIC, BNB, XRP, DOGE, SHIB, LTC, ATOM, XLM, GRT
    df = get_crypto_price(symbol='LRC', exchange='USD', start_date='2020-01-01')
    plot_exchange(df)