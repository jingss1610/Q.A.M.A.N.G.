import pandas as pd
import sys
import subprocess

file_path = 'recom_funda/all_stock_funda_indicators.csv'
df = pd.read_csv(file_path, index_col=0, encoding='utf-8-sig')
df = df.applymap(lambda x: x.replace(',', '') if isinstance(x, str) else x)

balance_file_path = 'recom_stmt/all_stock_balance.csv'
balance_df = pd.read_csv(balance_file_path, index_col=0, encoding='utf-8-sig')
balance_df = balance_df.applymap(lambda x: x.replace(',', '') if isinstance(x, str) else x)

cash_file_path = 'recom_stmt/all_stock_cash.csv'
cash_df = pd.read_csv(cash_file_path, index_col=0, encoding='utf-8-sig')
cash_df = cash_df.applymap(lambda x: x.replace(',', '') if isinstance(x, str) else x)

common_columns = df.columns.intersection(balance_df.columns)
df = df[common_columns]
balance_df = balance_df[common_columns]
cash_df = cash_df[common_columns]

df = df.apply(pd.to_numeric, errors='coerce')
balance_df = balance_df.apply(pd.to_numeric, errors='coerce')
cash_df = cash_df.apply(pd.to_numeric, errors='coerce')

balance_df.loc['Total Liabilities'] = balance_df.loc['Total Liabilities'].where(balance_df.loc['Total Liabilities'].notna(), 0)
balance_df.loc['부채'] = balance_df.loc['부채'].where(balance_df.loc['부채'].notna(), 0)
total_liability = (balance_df.loc['Total Liabilities'] + balance_df.loc['부채'])
df.loc['EV/FCF Liabilites'] = total_liability

balance_df.loc['Total Current Assets'] = balance_df.loc['Total Current Assets'].where(balance_df.loc['Total Current Assets'].notna(), 0)
balance_df.loc['Total Cash'] = balance_df.loc['Total Cash'].where(balance_df.loc['Total Cash'].notna(), 0)
balance_df.loc['현금및현금성자산'] = balance_df.loc['현금및현금성자산'].where(balance_df.loc['현금및현금성자산'].notna(), 0)
total_cash = (balance_df.loc['Total Current Assets'] + balance_df.loc['Total Cash'] + balance_df.loc['현금및현금성자산'])
df.loc['EV/FCF Cash'] = total_cash

ev = df.loc['EV/FCF Liabilites'] - df.loc['EV/FCF Cash'] + df.loc['Market Cap']
df.loc['EV'] = ev

cash_df.loc['영업활동으로인한현금흐름'] = cash_df.loc['영업활동으로인한현금흐름'].where(cash_df.loc['영업활동으로인한현금흐름'].notna(), 0)
cash_df.loc['투자활동으로인한현금흐름'] = cash_df.loc['투자활동으로인한현금흐름'].where(cash_df.loc['투자활동으로인한현금흐름'].notna(), 0)
fcf_ks200 = (cash_df.loc['영업활동으로인한현금흐름'] - cash_df.loc['투자활동으로인한현금흐름'])
cash_df.loc['Free Cash Flow'] = cash_df.loc['Free Cash Flow'].where(cash_df.loc['Free Cash Flow'].notna(), 0)
fcf = fcf_ks200 + cash_df.loc['Free Cash Flow']
df.loc['FCF'] = fcf

ev_to_fcf = df.loc['EV'] / df.loc['FCF']
df.loc['EV/FCF'] = ev_to_fcf

df.to_csv('recom_funda/all_stock_funda_indicators.csv', encoding='utf-8-sig')

fcf_condition_1 = df.loc['EV/FCF'] >= 0
fcf_condition_2 = df.loc['EV/FCF'] <= 10
roa_condition = df.loc['ROA'] >= 5
roe_condition = df.loc['ROE'] >= 15
roi_condition = df.loc['ROI'] >= 10
debt_eq_condition = df.loc['Debt/Eq'] <= 1
quick_condition = df.loc['Quick Ratio'] >= 100
profit_margin_condition = df.loc['Profit Margin'] >= 10

satisfying_rows = df.loc[:, fcf_condition_1 & fcf_condition_2 & roa_condition & roe_condition & roi_condition & debt_eq_condition & quick_condition & profit_margin_condition]

max_roe_column = satisfying_rows.loc['ROE'].idxmax()
top_roe_columns = satisfying_rows.loc['ROE'].nlargest(3)

portfolio_optimized_file = 'portfolio_list/portfolio_optimized.csv'
portfolio_optimized_df = pd.read_csv(portfolio_optimized_file, encoding='utf-8-sig')

# 1개
print(max_roe_column)
#new_row = {'Ticker': max_roe_column}
#portfolio_optimized_df = pd.concat([portfolio_optimized_df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

# 3개
print(', '.join(top_roe_columns.index))
new_rows = [{'Ticker': ticker} for ticker in top_roe_columns.index]
portfolio_optimized_df = pd.concat([portfolio_optimized_df, pd.DataFrame(new_rows)], ignore_index=True)

portfolio_recommended_file = 'portfolio_list/portfolio_recommended.csv'
portfolio_optimized_df.drop_duplicates(subset='Ticker', inplace=True)
portfolio_optimized_df.to_csv(portfolio_recommended_file, index=False, encoding='utf-8-sig')

subprocess.run(['python', 'portfolio_recom_price.py'])
sys.exit()
