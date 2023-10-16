import pandas as pd
import os
import numpy as np
import requests
from bs4 import BeautifulSoup
import sys
import subprocess

tickers = []
weights = []

for file in os.listdir('portfolio_list'):
    if file.endswith('.csv') and file.startswith('portfolio_selected'):
        filepath = os.path.join('portfolio_list', file)
        df = pd.read_csv(filepath, dtype={'Ticker': str})
        tickers += list(df['Ticker'])
        weights += list(df['Weight'])

folder_path = 'portfolio_price'
csv_updated = [f"{ticker}_updated.csv" for ticker in tickers]

dfs = []

for ticker, csv_file in zip(tickers, csv_updated):
    file_path = os.path.join(folder_path, csv_file)
    df = pd.read_csv(file_path, index_col='Date')
    df['Ticker'] = ticker
    dfs.append(df)

common_dates = dfs[0].index
for df in dfs[1:]:
    common_dates = common_dates.intersection(df.index)
dfs = [df.loc[common_dates] for df in dfs]

folder = 'backtesting'
portfolio_data = pd.read_csv(os.path.join(folder, 'portfolio_data.csv'), index_col='Date')

# CAGR, MDD
portfolio_prices = portfolio_data['P_Price_2']

n_days = len(portfolio_prices)
n_years = n_days / 252
cagr = ((portfolio_prices.iloc[-1] / portfolio_prices.iloc[0]) ** (1 / n_years) - 1) * 100

portfolio_prices = portfolio_data['P_Price_1']

cummax = portfolio_prices.cummax()
drawdown = (portfolio_prices - cummax) / cummax
mdd = drawdown.min() * 100

# 최고 연간 수익률, 최저 연간 수익률
portfolio_data['Year'] = pd.DatetimeIndex(portfolio_data.index).year
annual_return = portfolio_data.groupby('Year')['P_Return(D)'].sum()

best_year = annual_return.max()
worst_year = annual_return.min()

# 포트폴리오 기대 수익률
portfolio_E_return = portfolio_data['P_Return(D)'].mean() * 252

# 무위험이자율
url = 'https://stooq.com/q/?s=10kry.b'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
risk_free_rate = float(soup.find(id='aq_10kry.b_c3').text)

# 공분산, 상관계수, 하방위험
returns = pd.concat([df['Return(D)'] for df in dfs], axis=1)

if len(tickers) == 1:
    cov_matrix_df = pd.DataFrame({'cov': [np.var(returns)]}, index=tickers, columns=tickers)
    corr_matrix_df = pd.DataFrame({'corr': [1]}, index=tickers, columns=tickers)
else:
    cov_matrix = np.cov(returns, rowvar=False)
    cov_matrix_df = pd.DataFrame(cov_matrix, index=tickers, columns=tickers)
    corr_matrix = np.corrcoef(returns, rowvar=False)
    corr_matrix_df = pd.DataFrame(corr_matrix, index=tickers, columns=tickers)

neg_returns = pd.concat([df['Return(D)'][df['Return(D)'] < 0] for df in dfs], axis=1)
neg_returns_squared = neg_returns ** 2
neg_returns_squared_sum = neg_returns_squared.sum(skipna=True, numeric_only=True)
neg_returns_squared_sum = neg_returns_squared_sum.to_numpy().reshape(1, -1)
downside_risk = np.dot(weights, np.sqrt(neg_returns_squared_sum).T) / len([df['Return(D)'] for df in dfs] * 252)

# 포트폴리오 표준편차
std_returns = []

for df in dfs:
    std_returns.append(df['Return(D)'].std() * np.sqrt(252))

def portfolio_std_formula(weights, cov_matrix_df, corr_matrix_df):
    weights = weights / 100
    num_assets = len(weights)
    if num_assets == 1:
        portfolio_std = std_returns[0]
    else:
        sigmas = np.sqrt(np.diag(cov_matrix_df))
        first_term = np.sum(np.square(weights) * np.square(sigmas))
        second_term = 0
        for i in range(num_assets):
            for j in range(i + 1, num_assets):
                second_term += weights[i] * weights[j] * sigmas[i] * sigmas[j] * corr_matrix_df.iloc[i, j]
        portfolio_std = np.sqrt(first_term + 2 * second_term) * np.sqrt(252) * 100
    return portfolio_std
portfolio_std = portfolio_std_formula(np.array(weights) / 100, cov_matrix_df, corr_matrix_df)

# Sharpe Ratio, Sortino Ratio, Calmar Ratio
sharpe_ratio = (portfolio_E_return - risk_free_rate) / portfolio_std
sortino_ratio = (portfolio_E_return - risk_free_rate) / downside_risk
calmar_ratio = (portfolio_E_return - risk_free_rate) / abs(mdd)

backtesting_output = [portfolio_E_return, cagr, portfolio_std, best_year, worst_year, mdd, sharpe_ratio, sortino_ratio[0], calmar_ratio]
index = ['기대수익률', '연평균 성장률', '표준편차', '최고 연간 수익률', '최저 연간 수익률', '최대 낙폭', '샤프 비율', '소티노 비율', '칼마 비율']
backtesting_output = pd.DataFrame(backtesting_output, index=index)
backtesting_output = backtesting_output.round(2)
output_path = os.path.join(folder, 'backtesting_output.csv')
backtesting_output.to_csv(output_path, index=True, header=False, encoding='utf-8-sig')

print("")
print("※ 면 책 ※")
print("금융투자상품은 자산가격 변동, 환율 변동 등에 따라 투자원금의 손실이 발생할 수 있으며, 그 손실은 투자자에게 귀속됩니다.")
print("투자는 자신의 책임과 위험 부담에서 이루어지는 것이므로 사용자의 투자 결과에 대해 책임을 지지 않습니다.")
print("이 소프트웨어는 투자 결정의 근거로 사용하기 위한 것이 아니며, 완전하다고 가정해서는 안 됩니다.")

subprocess.run(['python', 'optimizing_1.py'])
sys.exit()
