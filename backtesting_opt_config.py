from pykrx import stock
from datetime import datetime, date
import FinanceDataReader as fdr
import yfinance as yf
import pandas as pd
import os
import numpy as np
import sys
import subprocess

tickers = []
weights = []

for file in os.listdir('portfolio_list'):
    if file.endswith('.csv') and file.startswith('portfolio_optimized'):
        filepath = os.path.join('portfolio_list', file)
        df = pd.read_csv(filepath, dtype={'Ticker': str})
        tickers += list(df['Ticker'])
        weights += list(df['Weight'])

folder_path = 'portfolio_price'
csv_list = [f"{ticker}_portfolio.csv" for ticker in tickers]

dfs = []

for ticker, csv_file in zip(tickers, csv_list):
    file_path = os.path.join(folder_path, csv_file)
    df = pd.read_csv(file_path, index_col='Date', encoding='utf-8-sig')
    df.index = pd.to_datetime(df.index)
    df['Date'] = df.index
    df['Ticker'] = ticker
    df['Re_Price'] = np.nan
    df['Return(D)'] = np.nan
    dfs.append(df)

common_dates_df = dfs[0].index
for df in dfs[1:]:
    common_dates_df = common_dates_df.intersection(df.index)
dfs = [df.loc[common_dates_df] for df in dfs]

benchmark_KS11 = fdr.DataReader('KS11')
benchmark_KS11 = benchmark_KS11.iloc[:, 4:5]

benchmark_KQ11 = fdr.DataReader('KQ11')
benchmark_KQ11 = benchmark_KQ11.iloc[:, 4:5]

benchmark_GSPC = yf.download("^GSPC")
benchmark_GSPC = benchmark_GSPC.iloc[:, 4:5]

benchmark_IXIC = yf.download("^IXIC")
benchmark_IXIC = benchmark_IXIC.iloc[:, 4:5]

for benchmark in [benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC]:
    benchmark.index.name = 'Date'
    benchmark['Date'] = benchmark.index
    benchmark.rename(columns={benchmark.columns[0]: 'Point'}, inplace=True)
benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC = [benchmark.set_index(pd.to_datetime(benchmark.index)) for benchmark in [benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC]]

common_dates_bench = [benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC][0].index
for benchmark in [benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC][1:]:
    common_dates_bench = common_dates_bench.intersection(benchmark.index)
[benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC] = [benchmark.loc[common_dates_bench] for benchmark in [benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC]]

common_index = common_dates_df.intersection(common_dates_bench)
df = df.loc[common_index]
benchmark = benchmark.loc[common_index]
dfs = [df.loc[common_index] for df in dfs]
benchmark_KS11 = benchmark_KS11.loc[common_index]
benchmark_KQ11 = benchmark_KQ11.loc[common_index]
benchmark_GSPC = benchmark_GSPC.loc[common_index]
benchmark_IXIC = benchmark_IXIC.loc[common_index]

for df in dfs:
    ticker = df['Ticker'].iloc[0]
    file_name = f"{ticker}_portfolio.csv"
    file_path = os.path.join(folder_path, file_name)
    df.to_csv(file_path, encoding='utf-8-sig')

folder = 'backtesting'
portfolio_config = pd.read_csv(os.path.join(folder, 'portfolio_config.csv'), header=None, index_col=0, encoding='utf-8-sig')

initial_amount = float(portfolio_config.loc['I_amount'][1])

for i, df in enumerate(dfs):
    price_col = df['Price']
    first_price = price_col.iloc[0]
    df['Price'] = price_col / first_price * initial_amount * weights[i] / 100

for benchmark in [benchmark_KS11, benchmark_KQ11, benchmark_GSPC, benchmark_IXIC]:
    benchmark_col = benchmark['Point']
    first_point = benchmark_col.iloc[0]
    benchmark['Point'] = benchmark_col / first_point * initial_amount

for df in dfs:
    df['Return(D)'] = df['Price'].pct_change().fillna(0) * 100

P_Price_3 = pd.concat([df['Price'] for df in dfs], axis=1).sum(axis=1)

P_Return_D = P_Price_3.pct_change().fillna(0) * 100

# Rebalancing
re_interval = portfolio_config.loc['Re_interval'].values[0]

if re_interval in ['year', 'half', 'quarter', 'month']:
    rebalancing_dates = []

    if re_interval == 'year':
        rebalancing_dates = [df.index[-1] for df in dfs]

    elif re_interval == 'half':
        for df in dfs:
            half_year_indices = df[df.index.month.isin([6, 12])].index
            rebalancing_dates.append(half_year_indices[-1])

    elif re_interval == 'quarter':
        for df in dfs:
            quarter_indices = df[df.index.month.isin([3, 6, 9, 12])].index
            rebalancing_dates.append(quarter_indices[-1])

    elif re_interval == 'month':
        for df in dfs:
            month_indices = df.groupby([df.index.year, df.index.month]).tail(1).index
            rebalancing_dates.extend(month_indices)

    rebalancing_df = pd.DataFrame({'Re_Dates': rebalancing_dates})
    rebalancing_df['Adj_Amount'] = np.nan

    for df in dfs:
        re_price_indices = df[df['Date'] < rebalancing_df['Re_Dates'].iloc[0]].index
        df.loc[re_price_indices, 'Re_Price'] = df.loc[re_price_indices, 'Price']

    for j in range(len(rebalancing_df) - 1):
        for df in dfs:
            rebalancing_date_start = rebalancing_df['Re_Dates'].iloc[j]
            rebalancing_date_end = rebalancing_df['Re_Dates'].iloc[j + 1]
            price_indices = (df['Date'] >= rebalancing_date_start) & (df['Date'] < rebalancing_date_end)
            df.loc[price_indices, 'Re_Price'] = df.loc[price_indices, 'Price']

            rebalancing_df.at[j, 'Adj_Amount'] = sum(df.loc[rebalancing_df['Re_Dates'].iloc[j], 'Price'] for df in dfs)
            for i, df in enumerate(dfs):
                first_price = df.loc[df['Date'] == rebalancing_df['Re_Dates'].iloc[j], 'Price'].values[0]
                adjusted_amount = rebalancing_df['Adj_Amount'].iloc[j]
                df.loc[df['Date'] >= rebalancing_df['Re_Dates'].iloc[j], 'Price'] = df[
                                                                                        'Price'] / first_price * adjusted_amount * \
                                                                                    weights[i] / 100

    for df in dfs:
        df.loc[rebalancing_df['Re_Dates'].iloc[-1]:, 'Re_Price'] = df.loc[rebalancing_df['Re_Dates'].iloc[-1]:, 'Price']

    for df in dfs:
        del df['Price']
        df.rename(columns={'Re_Price': 'Price'}, inplace=True)

# Cash Flow
CF_interval = portfolio_config.loc['CF_interval'].values[0]
CF_amount = float(portfolio_config.loc['CF_amount'].values[0])

if CF_interval in ['year', 'half', 'quarter', 'month']:
    cf_dates = []

    if CF_interval == 'year':
        cf_dates = [df.index[-1] for df in dfs]

    elif CF_interval == 'half':
        for df in dfs:
            half_year_indices = df[df.index.month.isin([6, 12])].index
            cf_dates.append(half_year_indices[-1])

    elif CF_interval == 'quarter':
        for df in dfs:
            quarter_indices = df[df.index.month.isin([3, 6, 9, 12])].index
            cf_dates.append(quarter_indices[-1])

    elif CF_interval == 'month':
        for df in dfs:
            month_indices = df.groupby([df.index.year, df.index.month]).tail(1).index
            cf_dates.extend(month_indices)

    cf_df = pd.DataFrame({'CF_Dates': cf_dates})

    for i, df in enumerate(dfs):
        cf_price_indices = df[df['Date'].isin(cf_df['CF_Dates'])].index
        for index in cf_price_indices:
            df.loc[index:, 'Price'] += CF_amount * weights[i] / 100

for df in dfs:
    ticker = df['Ticker'].iloc[0]
    file_name = f"{ticker}_optimized.csv"
    file_path = os.path.join(folder_path, file_name)
    df.drop('Date', axis=1, inplace=True)
    df.drop('Ticker', axis=1, inplace=True)
    df.to_csv(file_path, encoding='utf-8-sig')

P_Price_4 = pd.concat([df['Price'] for df in dfs], axis=1).sum(axis=1)

portfolio_data = pd.DataFrame({'P_Price_3': P_Price_3, 'P_Price_4': P_Price_4, 'P_Return(D)': P_Return_D})

if portfolio_data['P_Price_4'].isna().any():
    portfolio_data.drop(portfolio_data.index[0], inplace=True)

portfolio_data.to_csv('backtesting/portfolio_opt_data.csv', index=True, encoding='utf-8-sig')

subprocess.run(['python', 'backtesting_opt_main.py'])
sys.exit()
