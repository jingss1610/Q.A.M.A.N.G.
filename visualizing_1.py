import pandas as pd
import os
from datetime import date
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

portfolio_data = []

for file in os.listdir('backtesting'):
    if file.endswith('.csv') and file.startswith('portfolio_data'):
        filepath = os.path.join('backtesting', file)
        df = pd.read_csv(filepath, index_col='Date')
        portfolio_data.append(df)

P_Price_2 = pd.DataFrame()
for df in portfolio_data:
    P_Price_2_df = df[['P_Price_2']]
    P_Price_2 = pd.concat([P_Price_2, P_Price_2_df], axis=1)
P_Price_2.index = pd.to_datetime(P_Price_2.index)

benchmarks_data = pd.read_csv('backtesting/benchmarks_data.csv', index_col='Date', parse_dates=['Date'])
benchmarks_data = benchmarks_data[['KOSPI', 'KOSDAQ', 'S&P 500', 'NASDAQ']]

Price_Points = pd.concat([P_Price_2['P_Price_2'], benchmarks_data['KOSPI'], benchmarks_data['KOSDAQ'], benchmarks_data['S&P 500'], benchmarks_data['NASDAQ']], axis=1)
Price_Points.columns = ['Portfolio', 'KOSPI', 'KOSDAQ', 'S&P 500', 'NASDAQ']

empty_cols = Price_Points.columns[Price_Points.iloc[0].isnull()]
Price_Points.dropna(axis=0, how='any', subset=empty_cols, inplace=True)

# 차트
mpl.rcParams['font.family'] = 'Malgun Gothic'

portfolio_info = pd.read_csv('portfolio_list/portfolio_selected.csv')
tickers = portfolio_info['Ticker']
weights = portfolio_info['Weight']

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, figsize=(16, 9), gridspec_kw={'width_ratios': [13, 3], 'height_ratios': [8, 1]})
figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()

# ax1
for col in Price_Points.columns:
    ax1.semilogy(Price_Points.index, Price_Points[col], label=col)

ax1.set_xlabel('Date')
ax1.set_ylabel('Portfolio Balance(₩)')
today = date.today().strftime("%Y-%m-%d")
ax1.set_title(f'Backtesting Result\n({today})')
ax1.legend(loc='upper left')

for val in ax1.get_yticks():
    ax1.axhline(y=val, linewidth=0.1, color='gray')

for date in pd.date_range(start=Price_Points.index[0], end=Price_Points.index[-1], freq='Q'):
    ax1.axvline(x=date, linewidth=0.1, color='gray')

portfolio_label = f'₩{Price_Points.iloc[-1]["Portfolio"]:,.0f}'
ax1.text(Price_Points.index[-1], Price_Points.iloc[-1]['Portfolio']*1.25, portfolio_label, ha='center', va='center')

ax1.set_yscale('log')

yticks = ax1.get_yticks()
new_yticks = [int(np.power(10, y)) for y in np.log10(yticks)]
new_yticks_half = []
for i in range(len(new_yticks)-1):
    half = int((new_yticks[i + 1]) / 2)
    new_yticks_half.append(half)
    ax1.axhline(y=half, linewidth=0.1, color='gray')
new_yticks_all = sorted(list(set(new_yticks + new_yticks_half)))
new_yticklabels = []
for x in new_yticks_all:
    if x >= 1000000:
        new_yticklabels.append(f'{x//1000000:,.0f}M')
    else:
        new_yticklabels.append(f'{x//100000:,.0f}K')
ax1.set_yticks(new_yticks_all)
ax1.set_yticklabels(new_yticklabels)

y_min = 15 ** (np.floor(np.log10(Price_Points.min().min())))
y_max = 10 ** (np.ceil(np.log10(Price_Points.max().max())))
ax1.set_ylim([y_min, y_max])

# ax2
palette = sns.color_palette('Set3')
ax2.pie(weights, labels=tickers, autopct='%1.0f%%', colors=palette,
        wedgeprops={'edgecolor': 'black', 'linewidth': 1})
ax2.set_title('Portfolio Configuration')

table_data = []

for file in os.listdir('backtesting'):
    if file.endswith('.csv') and file.startswith('portfolio_config'):
        filepath = os.path.join('backtesting', file)
        portfolio_config = pd.read_csv(filepath, encoding='utf-8-sig', header=None)
        portfolio_config = portfolio_config.astype(str)
        portfolio_config.iloc[0, 0] = '최초잔고'
        portfolio_config.iloc[1, 0] = '정기 입출금 주기'
        portfolio_config.iloc[2, 0] = '입출금 설정액'
        portfolio_config.iloc[3, 0] = '리밸런싱 주기'
        portfolio_config.iloc[0, 1] = '₩' + '{:,.0f}'.format(float(portfolio_config.iloc[0, 1]))
        portfolio_config.iloc[2, 1] = '₩' + '{:,.0f}'.format(float(portfolio_config.iloc[2, 1]))

        for index, value in portfolio_config.iterrows():
            if value[1] == 'year':
                portfolio_config.iloc[index, 1] = '년'
            elif value[1] == 'half':
                portfolio_config.iloc[index, 1] = '반기'
            elif value[1] == 'quarter':
                portfolio_config.iloc[index, 1] = '분기'
            elif value[1] == 'month':
                portfolio_config.iloc[index, 1] = '월'

        for _, row in portfolio_config.iterrows():
            table_data.append(row.tolist())

final = [['최종잔고', f'₩{Price_Points.iloc[-1]["Portfolio"]:,.0f}']]
for row in final:
    table_data.append(row)

for file in os.listdir('backtesting'):
    if file.endswith('.csv') and file.startswith('backtesting_output'):
        filepath = os.path.join('backtesting', file)
        W_backtesting_output = pd.read_csv(filepath, encoding='utf-8-sig', header=None)
        W_backtesting_output = W_backtesting_output.astype(str)
        W_backtesting_output.iloc[:-3, 1] = W_backtesting_output.iloc[:-3, 1].apply(lambda x: x + '%')
        for _, row in W_backtesting_output.iterrows():
            table_data.append(row.tolist())

table = ax2.table(cellText=table_data, loc='bottom')
table.scale(1, 4)
table.auto_set_font_size(False)
table.set_fontsize(10)

ax2.set_aspect('equal', anchor=(0, 1))
ax2.axes.get_xaxis().set_visible(False)
ax2.axes.get_yaxis().set_visible(False)

# ax3
ax3.axis('off')
ax3.text(0, 1, '※ 면 책 ※\n\n금융투자상품은 자산가격 변동, 환율 변동 등에 따라 투자원금의 손실이 발생할 수 있으며, 그 손실은 투자자에게 귀속됩니다.'
                   '\n투자는 자신의 책임과 위험 부담에서 이루어지는 것이므로 사용자의 투자 결과에 대해 책임을 지지 않습니다.'
                   '\n이 소프트웨어는 투자 결정의 근거로 사용하기 위한 것이 아니며, 완전하다고 가정해서는 안 됩니다.',
         ha='left', va='center', fontsize=12, fontweight='bold', linespacing=1.5)
ax3.set_aspect('equal', anchor=(0, 1))
ax3.axes.get_xaxis().set_visible(False)
ax3.axes.get_yaxis().set_visible(False)

# ax4
ax4.axis('off')
ax4.axes.get_xaxis().set_visible(False)
ax4.axes.get_yaxis().set_visible(False)

plt.tight_layout()
plt.show()
