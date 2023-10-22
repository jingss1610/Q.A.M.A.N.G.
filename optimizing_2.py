import pandas as pd
import os
import numpy as np
import yfinance as yf
import cvxpy as cp
from scipy.optimize import minimize
import requests
from bs4 import BeautifulSoup
import csv
import sys
import subprocess

tickers = []

for file in os.listdir('portfolio_list'):
    if file.endswith('.csv') and file.startswith('portfolio_recommended'):
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

common_dates_df = dfs[0].index
for df in dfs[1:]:
    common_dates_df = common_dates_df.intersection(df.index)
dfs = [df.loc[common_dates_df] for df in dfs]

for df in dfs:
    df['Return(D)'] = df['Price'].pct_change().fillna(0) * 100

num_assets = len(tickers)
initial_weights = np.array([1/num_assets] * num_assets)

returns = pd.concat([df['Return(D)'] for df in dfs], axis=1)

if len(tickers) == 1:
    cov_matrix_df = pd.DataFrame({'cov': [np.var(returns)]}, index=tickers, columns=tickers)
else:
    cov_matrix = np.cov(returns, rowvar=False)
    cov_matrix_df = pd.DataFrame(cov_matrix, index=tickers, columns=tickers)

returns = returns.div(len(dfs)).mul(252)
mean_returns = returns.mean()
cov_matrix = cov_matrix_df.to_numpy()

benchmark_GSPC = yf.download('^GSPC')
benchmark_GSPC['Return(I)'] = benchmark_GSPC['Adj Close'].pct_change().dropna()

common_dates_bench = benchmark_GSPC.index

common_index = common_dates_df.intersection(common_dates_bench)
df = df.loc[common_index]
dfs = [df.loc[common_index] for df in dfs]
benchmark_GSPC = benchmark_GSPC.loc[common_index]

daily_volatility = benchmark_GSPC['Return(I)'].std()
target_risk = daily_volatility

weights = cp.Variable(num_assets)
portfolio_risk = cp.quad_form(weights, cov_matrix)

constraints = [cp.sum(weights) == 1, weights >= 0]
objective = cp.Minimize(portfolio_risk)
problem = cp.Problem(objective, constraints)
problem.solve()

optimal_weights = [round(weight * 100, 2) for weight in weights.value]

for i in range(len(tickers)):
    print(tickers[i], optimal_weights[i])

filtered_data = [(ticker, weight) for ticker, weight in zip(tickers, optimal_weights) if weight != 0]
tickers_filtered, optimal_weights_filtered = zip(*filtered_data)
folder_path = 'portfolio_list'
csv_file_path = os.path.join(folder_path, 'portfolio_recommended.csv')
with open(csv_file_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=['Ticker', 'Weight'])
    writer.writeheader()
    for row in zip(tickers_filtered, optimal_weights_filtered):
        writer.writerow({'Ticker': row[0], 'Weight': row[1]})

subprocess.run(['python', 'backtesting_opt_config.py'])
sys.exit()
