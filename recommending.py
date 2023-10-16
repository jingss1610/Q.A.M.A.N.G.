import pandas as pd
import sys
import subprocess

file_path = 'recom_funda/all_stock_funda_indicators.csv'
df = pd.read_csv(file_path, index_col=0, encoding='utf-8-sig')

df = df.apply(pd.to_numeric, errors='coerce')

roe_condition = df.loc['ROE'] >= 30
roi_condition = df.loc['ROI'] >= 25
debt_eq_condition = df.loc['Debt/Eq'] <= 1

satisfying_rows = df.loc[:, roe_condition & roi_condition & debt_eq_condition]

max_profit_margin_column = satisfying_rows.loc['Profit Margin'].idxmax()
top_profit_margin_columns = satisfying_rows.loc['Profit Margin'].nlargest(3)

portfolio_optimized_file = 'portfolio_list/portfolio_optimized.csv'
portfolio_optimized_df = pd.read_csv(portfolio_optimized_file, encoding='utf-8-sig')

# 1개
print(max_profit_margin_column)
#new_row = {'Ticker': max_profit_margin_column}
#portfolio_optimized_df = pd.concat([portfolio_optimized_df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

# 3개
print(', '.join(top_profit_margin_columns.index))
new_rows = [{'Ticker': ticker} for ticker in top_profit_margin_columns.index]
portfolio_optimized_df = pd.concat([portfolio_optimized_df, pd.DataFrame(new_rows)], ignore_index=True)

portfolio_recommended_file = 'portfolio_list/portfolio_recommended.csv'
portfolio_optimized_df.drop_duplicates(subset='Ticker', inplace=True)
portfolio_optimized_df.to_csv(portfolio_recommended_file, index=False, encoding='utf-8-sig')

subprocess.run(['python', 'portfolio_recom_price.py'])
sys.exit()
