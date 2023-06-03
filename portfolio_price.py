from pykrx import stock
from datetime import datetime
import FinanceDataReader as fdr
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import shutil
import subprocess
import sys

tickers = []
weights = []

for file in os.listdir('portfolio_list'):
    if file.endswith('.csv') and file.startswith('portfolio_selected'):
        filepath = os.path.join('portfolio_list', file)
        df = pd.read_csv(filepath, dtype={'Ticker': str})
        tickers += list(df['Ticker'])
        weights += list(df['Weight'])

folder = 'portfolio_price'
if os.path.exists(folder):
    shutil.rmtree(folder)
os.mkdir(folder)

for i, (ticker, weight) in enumerate(zip(tickers, weights)):
    print(f"{i + 1}: {ticker.upper()}, 비중 {weight}%")

for ticker, weight in zip(tickers, weights):
#    if re.match(r'^\d{6}$', ticker):  # 한국
#        data = stock.get_market_ohlcv_by_date("00000000", f"{datetime.today().strftime('%Y%m%d')}", ticker)
#        if not data.empty:
#            data.index.name = 'Date'
#            data = data[['종가']]
#            data.rename(columns={'종가': 'Price'}, inplace=True)
#            file_path = os.path.join(folder, f'{ticker.upper()}_portfolio.csv')
#            data.to_csv(file_path, encoding='utf-8-sig')
#        if data.empty:
#            data = stock.get_etf_ohlcv_by_date("00000000", f"{datetime.today().strftime('%Y%m%d')}", ticker)
#            data.index.name = 'Date'
#            data = data[['종가']]
#            data.rename(columns={'종가': 'Price'}, inplace=True)
#            file_path = os.path.join(folder, f'{ticker.upper()}_portfolio.csv')
#            data.to_csv(file_path, encoding='utf-8-sig')
#            if data.empty:
#                print(f"{ticker} 종목을 찾지 못했습니다.")

    if re.match(r'^\d{6}$', ticker):  # 한국
        data = fdr.DataReader(ticker)
        if data.empty:
            print(f"{ticker} 종목을 찾지 못했습니다.")
        else:
            data = data[['Close']].rename(columns={'Close': 'Price'})
            file_path = os.path.join(folder, f'{ticker.upper()}_portfolio.csv')
            data.to_csv(file_path, encoding='utf-8-sig')

    elif re.match(r'^[a-zA-Z]{1,6}$|^\d{4}$', ticker, flags=re.IGNORECASE):  # 미국, 일본
        if re.match(r'^[a-zA-Z]{1,6}$', ticker):
            us_ticker = ticker
            jp_ticker = None
        elif re.match(r'^\d{4}$', ticker):
            us_ticker = None
            jp_ticker = ticker + ".T"

        if us_ticker is not None:
            us_data = yf.download(us_ticker, period='MAX')
            if us_data.empty:
                print(f"{us_ticker} 종목을 찾지 못했습니다.")
            else:
                us_data = us_data[['Adj Close']].rename(columns={'Adj Close': 'Price'})
                file_path = os.path.join(folder, 'USDKRW_portfolio.csv')
                url = "https://stooq.com/q/d/l/?s=usdkrw&i=d"
                response = requests.get(url)
                with open(file_path, "wb") as f_usdkrw:
                    f_usdkrw.write(response.content)
                usdkrw_df = pd.read_csv(file_path, index_col="Date", usecols=["Date", "Close"])
                usdkrw_df.index = pd.to_datetime(usdkrw_df.index)
                us_data = us_data.ffill()
                usdkrw_df = usdkrw_df.ffill()
                df = pd.concat([us_data, usdkrw_df], axis=1, join='inner')
                df['Price'] = df['Price'] * df['Close'].fillna(method='ffill')
                file_path = os.path.join(folder, f'{us_ticker.upper()}_portfolio.csv')
                df[['Price']].to_csv(file_path, encoding='utf-8-sig')

        if jp_ticker is not None:
            jp_data = yf.download(jp_ticker, period='MAX')
            if jp_data.empty:
                print(f"{jp_ticker} 종목을 찾지 못했습니다.")
            else:
                jp_data = jp_data[['Adj Close']].rename(columns={'Adj Close': 'Price'})
                file_path = os.path.join(folder, 'JPYKRW_portfolio.csv')
                url = "https://stooq.com/q/d/l/?s=jpykrw&i=d"
                response = requests.get(url)
                with open(file_path, "wb") as f_jpykrw:
                    f_jpykrw.write(response.content)
                jpykrw_df = pd.read_csv(file_path, index_col="Date", usecols=["Date", "Close"])
                jpykrw_df.index = pd.to_datetime(jpykrw_df.index)
                jp_data = jp_data.ffill()
                jpykrw_df = jpykrw_df.ffill()
                df = pd.concat([jp_data, jpykrw_df], axis=1, join='inner')
                df['Price'] = df['Price'] * df['Close'].fillna(method='ffill')
                jp_ticker_without_dot_T = jp_ticker.replace('.T', '')
                file_path = os.path.join(folder, f'{jp_ticker_without_dot_T.upper()}_portfolio.csv')
                df[['Price']].to_csv(file_path, encoding='utf-8-sig')

    elif re.match(r'[a-zA-Z]+-?krw', ticker, flags=re.IGNORECASE):  # 암호화폐
        data = yf.download(ticker, period='MAX')
        if data.empty:
            print(f"{ticker} 종목을 찾지 못했습니다.")
        else:
            data = data[['Adj Close']].rename(columns={'Adj Close': 'Price'})
            file_path = os.path.join(folder, f'{ticker.upper()}_portfolio.csv')
            data.to_csv(file_path, encoding='utf-8-sig')

    elif re.match(r'금', ticker):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        gold_page_list = []
        page = 1
        while True:
            url = f'https://finance.naver.com/marketindex/goldDailyQuote.naver?&page={page}'
            response = requests.get(url)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'class': 'tbl_exchange'})
            rows = table.find_all('tr')[2:]
            if len(rows) == 0:
                break
            for row in rows:
                cells = row.find_all('td')
                data = {'Date': cells[0].text.strip(), 'Price': cells[1].text.strip()}
                gold_page_list.append(data)
            page += 1
        data = pd.DataFrame(gold_page_list)
        data['Date'] = pd.to_datetime(data['Date'], format='%Y.%m.%d').dt.strftime('%Y-%m-%d')
        data['Price'] = data['Price'].str.replace(',', '').str.replace('"', '').astype(float)
        data = data.sort_values(by='Date')
        data = data.set_index('Date')
        file_path = os.path.join(folder, f'{ticker}_portfolio.csv')
        data.to_csv(file_path, encoding='utf-8-sig')

subprocess.run(['python', 'portfolio_config.py'])
sys.exit()
