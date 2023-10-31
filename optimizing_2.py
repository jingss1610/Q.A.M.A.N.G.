import pandas as pd
import os
import numpy as np
from scipy.optimize import minimize
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

def objective(weights):
    portfolio_return = np.sum(mean_returns * weights) * 252
    portfolio_stddev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    sharpe_ratio = portfolio_return / portfolio_stddev
    return -sharpe_ratio

constraints = (
    {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1},
    {'type': 'ineq', 'fun': lambda weights: weights}
)

initial_guess = np.array([1/num_assets] * num_assets)

result = minimize(objective, initial_guess, method='SLSQP', constraints=constraints)

optimal_weights = result.x

min_weight_threshold = 0.01
filtered_tickers = [ticker for ticker, weight in zip(tickers, optimal_weights) if weight >= min_weight_threshold]
filtered_weights = [weight for weight in optimal_weights if weight >= min_weight_threshold]

for ticker, weight in zip(filtered_tickers, filtered_weights):
    print(f"{ticker}: {weight:.2%}")

folder_path = 'portfolio_list'
csv_file_path = os.path.join(folder_path, 'portfolio_recommended.csv')
with open(csv_file_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=['Ticker', 'Weight'])
    writer.writeheader()
    for row in zip(filtered_tickers, filtered_weights):
        weight_formatted = round(row[1] * 100, 2)
        writer.writerow({'Ticker': row[0], 'Weight': weight_formatted})

subprocess.run(['python', 'backtesting_opt_config.py'])
sys.exit()
