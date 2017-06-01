import pandas as pd
import matplotlib.pyplot as plt
import urllib.request, urllib.parse, urllib.error
import numpy as np
import datetime
import requests
from os import path


GOOGLE = 'google'

base_url={}
base_url[GOOGLE] = "http://www.google.com/finance/historical?output=csv&q="

dates_param = {}
dates_param[GOOGLE] = '&startdate={0}&enddate={1}'

def get_cookie_crumb():
    '''
    This function perform a query and extract the matching cookie and crumb.
    '''

    # Perform a Yahoo financial lookup on SP500
    url = 'https://finance.yahoo.com/quote/^GSPC'
    r = requests.get(url)
    alines = r.text
    cookies = r.cookies

    # Extract the crumb from the response
    cs = alines.find('CrumbStore')
    cr = alines.find('crumb', cs + 10)
    cl = alines.find(':', cr + 5)
    q1 = alines.find('"', cl + 1)
    q2 = alines.find('"', q1 + 1)
    crumb = alines[q1 + 1:q2]

    return crumb, cookies


def make_new_yahoo_url(ticker, dates, info='quote'):
    '''
    This function load the corresponding history/divident/split from Yahoo.
    '''
    # Check to make sure that the cookie and crumb has been loaded
    _crumb,_cookies = get_cookie_crumb()

    # Prepare the parameters and the URL
    # tb = datetime(int(begindate[0:4]), int(begindate[4:6]), int(begindate[6:8]), 0, 0)
    # te = datetime(int(enddate[0:4]), int(enddate[4:6]), int(enddate[6:8]), 0, 0)
    tb = dates[0]
    te = dates[-1]

    param = dict()
    param['period1'] = int(tb.timestamp())
    param['period2'] = int(te.timestamp())
    param['interval'] = '1d'
    if info == 'quote':
        param['events'] = 'history'
    elif info == 'dividend':
        param['events'] = 'div'
    elif info == 'split':
        param['events'] = 'split'
    param['crumb'] = _crumb
    params = urllib.parse.urlencode(param)
    url = 'https://query1.finance.yahoo.com/v7/finance/download/{}?{}'.format(ticker, params)
    r = requests.get(url,cookies=_cookies)

    print(r.status_code)
    print(r.text)

    return url, _cookies


def make_url(ticker_symbol, dates):
    params = ticker_symbol
    params = params + dates_param[GOOGLE].format(dates[0].strftime('%b+%d,%Y'), dates[-1].strftime('%b+%d,%Y'))
    return base_url[GOOGLE] + params


def symbol_to_path(symbol, dates):
    """Return CSV file path given ticker symbol."""
    return make_url(symbol, dates)
    #return _make_new_yahoo_url(symbol, dates)


def get_data(symbols, dates, columns=['Close']):

    if type(symbols) == str:
        symbols = [symbols]

    panel = {}

    for c in columns:
        for symbol in symbols:

            filename = 'data/' + c + '/' + symbol.replace(':','_') + '.csv'

            if path.exists(filename):
                df = pd.read_csv(filename, index_col='Date', parse_dates=True, usecols=['Date', symbol])
                print(dates)
                dates = dates.drop(dates[dates <= np.amax(df.index)])
            else:
                df = pd.DataFrame(index=dates)
            dates = dates.drop(datetime.datetime.now().date())
            print('dates')
            print(dates)
            print('---')

            if len(dates) > 0:
                print("Getting {1} items from {0}".format(symbol_to_path(symbol, dates), len(dates)))
                df_temp = pd.read_csv(symbol_to_path(symbol, dates), index_col='Date', parse_dates=True, usecols=['Date', c])
                df_temp = df_temp.rename(columns={c: symbol})
                print(df_temp.head())
                print(df.head())
                if symbol in df.columns:
                    print('if')
                    df = df.append(df_temp)
                else:
                    print('else')
                    df = df.join(df_temp)

                #df.fillna(inplace=True, method='ffill')
                #df.fillna(inplace=True, method='bfill')
                df.dropna(inplace=True)

                df.to_csv(filename, index_label='Date')

            panel[c] = df

    if len(panel) == 1:
        panel = list(panel.values())[0]

    return panel


if __name__ == '__main__':
    print('plinio lindo')
    dates = pd.date_range('2014-06-01', 'today')
    p = get_data('INDEXBVMF:IBOV', dates) # TODO accept more than one stock
    if type(p) == dict:
        for df in p.values():
            df.plot()
    else:
        p.plot()

    plt.show()
