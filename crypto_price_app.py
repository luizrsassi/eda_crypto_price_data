import streamlit as st
from PIL import Image
import pandas as pd
import base64
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import json
import time

st.set_page_config(layout="wide")

image = Image.open('logo.jpg')

# use_column_width=True
st.image(image, width=500)

st.title("Crypto Price App")
st.markdown("""
This app retrives cryptocurrency prices for the top 100 cryptocurrency from the **CoinMarketCap!**
""")

expander_bar = st.expander("About")
expander_bar.markdown("""
* **Python libraries:** base64, json, pandas, requests, streamlit, time, BeautifulSoup, requests, json, time
* **Data Source:** [CoinMarketCap](https://coinmarketcap.com/)
* **Credit:** Web scraper adapted from the Medium article [Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* written by [Bryan Feng](https://medium.com/@bryanf).
""")

col1 = st.sidebar
col2, col3 = st.columns((2,1))

col1.header('Input Options')

currency_price_unit = col1.selectbox('Select currency for price', ('USD', 'BTC', 'ETH'))

@st.cache_data
def load_data():
    url = "https://coinmarketcap.com/"

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extracting the table from the HTML
    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coin_data = json.loads(data.contents[0])
    data_ = json.loads(coin_data['props']['initialState'])
    data = data_['cryptocurrency']['listingLatest']['data']

    headers = data[0]['keysArr']
    body = data[1:]

    item_headers = []
    for i in range(len(headers)):
        item_headers.append([])

    for i in range(len(body)):
        for j in range(len(item_headers)):
            item_headers[j].append(body[i][j])

    coins = dict()
    for i in range(len(headers)):
        coins[headers[i]] = item_headers[i]

    coins['coin_name'] = coins.pop('id')
    coins['coin_symbol'] = coins.pop('symbol')
    coins['market_cap'] = coins.pop('quote.USD.marketCap')
    coins['percent_change_1h'] = coins.pop('quote.USD.percentChange1h')
    coins['percent_change_24h'] = coins.pop('quote.USD.percentChange24h')
    coins['percent_change_7d'] = coins.pop('quote.USD.percentChange7d')
    coins['price'] = coins.pop('quote.USD.price')
    coins['volume_24h'] = coins.pop('quote.USD.volume24h')

    df_ = pd.DataFrame(coins)
    df = df_.loc[:,['coin_name', 'coin_symbol', 'market_cap', 'percent_change_1h', 'percent_change_24h',
                   'percent_change_7d', 'price', 'volume_24h']]

    return df
    

df = load_data()

## Sidebar - Cryptocurrency selections
sorted_coin = sorted(df['coin_symbol'])
selected_coin = col1.multiselect('Cryptocurrency', sorted_coin, sorted_coin)

df_selected_coin = df[df['coin_symbol'].isin(selected_coin)]

## Sidebar - Number of coins to display
num_coin = col1.slider('Display Top N Coins', 1, 100, 100)
df_coins = df_selected_coin[:num_coin]

## Sidebar - Percent change timeframe
percent_timeframe = col1.selectbox('Percent change time frame', ['7d', '24h', '1h'])
percent_dict = {"7d":"percent_change_7d", "24h":"percent_change_24h", "1h":"percent_change_1h"}
selected_percent_timeframe = percent_dict[percent_timeframe]

## Sidebar - Sorting values
sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])

col2.subheader('Price data of selected cryptocurrency')
col2.write('Data dimension: ' + str(df_coins.shape[0]) + ' rows and ' + str(df_coins.shape[1]) + ' columns.')

col2.dataframe(df_coins)

# Download CSV data
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto_price_app.csv">Download CSV file</a>'
    return href

col2.markdown(filedownload(df_coins), unsafe_allow_html=True)

#---------------------------------#
# Preparing data for Bar plot of % Price change
col2.subheader('Table of % price change')
df_change = pd.concat([df_coins.coin_symbol, df_coins.percent_change_1h, df_coins.percent_change_24h, df_coins.percent_change_7d], axis=1)
df_change = df_change.set_index('coin_symbol')
df_change['positive_percent_change_1h'] = df_change['percent_change_1h'] > 0
df_change['positive_percent_change_24h'] = df_change['percent_change_24h'] > 0
df_change['positive_percent_change_7d'] = df_change['percent_change_7d'] > 0
col2.dataframe(df_change)

# Conditional creation of Bar plot (time frame)
col3.subheader('Bar plot of % price change')

if percent_timeframe == '7d':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_7d'])
    col3.write('*7 days pedriod*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percent_change_7d'].plot(kind='barh', color=df_change.positive_percent_change_7d.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
elif percent_timeframe == '24h':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_24h'])
    col3.write('*24 hours period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percent_change_24h'].plot(kind='barh', color=df_change.positive_percent_change_24h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
else:
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_1h'])
    col3.write('*1 hour period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percent_change_1h'].plot(kind='barh', color=df_change.positive_percent_change_1h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
