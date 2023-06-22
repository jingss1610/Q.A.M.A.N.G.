import pandas as pd
import os
import numpy as np
import requests
from bs4 import BeautifulSoup
import sys
import subprocess

tickers = []

for file in os.listdir('portfolio_list'):
    if file.endswith('.csv') and file.startswith('portfolio_selected'):
        filepath = os.path.join('portfolio_list', file)
        df = pd.read_csv(filepath, dtype={'Ticker': str})
        tickers += list(df['Ticker'])

folder_path = 'portfolio_price'
csv_list = [f"{ticker}_portfolio.csv" for ticker in tickers]

dfs = []

for ticker, csv_file in zip(tickers, csv_list):
    file_path = os.path.join(folder_path, csv_file)
    df = pd.read_csv(file_path, index_col='Date', encoding='utf-8-sig')
    df.index = pd.to_datetime(df.index)
    df['Date'] = df.index
    df['Ticker'] = ticker
    df['Return(D)'] = np.nan
    dfs.append(df)

for df in dfs:
    df['Return(D)'] = df['Price'].pct_change().fillna(0) * 100

    print(df['Return(D)'])