import pandas as pd
import os
import numpy as np
from scipy.optimize import minimize
import requests
from bs4 import BeautifulSoup
import csv
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

common_dates_df = dfs[0].index
for df in dfs[1:]:
    common_dates_df = common_dates_df.intersection(df.index)
dfs = [df.loc[common_dates_df] for df in dfs]

for df in dfs:
    df['Return(D)'] = df['Price'].pct_change().fillna(0) * 100

num_assets = len(tickers)
initial_weights = np.array([1/num_assets] * num_assets)

# 무위험이자율
url = 'https://stooq.com/q/?s=10kry.b'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
risk_free_rate = float(soup.find(id='aq_10kry.b_c3').text)

returns = pd.concat([df['Return(D)'] for df in dfs], axis=1)

if len(tickers) == 1:
    cov_matrix_df = pd.DataFrame({'cov': [np.var(returns)]}, index=tickers, columns=tickers)
else:
    cov_matrix = np.cov(returns, rowvar=False)
    cov_matrix_df = pd.DataFrame(cov_matrix, index=tickers, columns=tickers)

returns = returns.div(len(dfs)).mul(252)
mean_returns = returns.mean()
cov_matrix = cov_matrix_df.to_numpy()

def sharpe_ratio_objective(weights, mean_returns, cov_matrix, risk_free_rate):
    portfolio_return = np.sum(mean_returns * weights)
    portfolio_stddev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_stddev
    return -sharpe_ratio

constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
bounds = tuple((0, 1) for asset in range(num_assets))

optimal_weights = minimize(sharpe_ratio_objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints, args=(mean_returns, cov_matrix, risk_free_rate))
optimal_weights = optimal_weights.x

optimal_portfolio_return = np.sum(mean_returns * optimal_weights)
optimal_portfolio_stddev = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
optimal_sharpe_ratio = (optimal_portfolio_return - risk_free_rate) / optimal_portfolio_stddev

optimal_weights_rounded = [round(weight * 100, 2) for weight in optimal_weights]
filtered_data = [(ticker, weight) for ticker, weight in zip(tickers, optimal_weights_rounded) if weight != 0]
tickers_filtered, optimal_weights_filtered = zip(*filtered_data)
folder_path = 'portfolio_list'
csv_file_path = os.path.join(folder_path, 'portfolio_optimized.csv')
with open(csv_file_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=['Ticker', 'Weight'])
    writer.writeheader()
    for row in zip(tickers_filtered, optimal_weights_filtered):
        writer.writerow({'Ticker': row[0], 'Weight': row[1]})

subprocess.run(['python', 'backtesting_opt_config.py'])
sys.exit()
