import pandas as pd
import os
import subprocess
import sys

initial_amount = int(input("최초잔고: "))
while initial_amount <= 0:
    initial_amount = int(input("최초잔고 설정액은 양의 정수여야 합니다. 최초잔고: "))

portfolio_cashflows = input("정기 입출금 여부를 알려주세요. [y/n] ")
if portfolio_cashflows == "y":
    cashflows_interval = input("입출금 주기를 선택해주세요. 1:월 / 2:분기 / 3:반기 / 4:년 ")
    while cashflows_interval not in ["1", "2", "3", "4"]:
        cashflows_interval = input("입출금 주기를 선택해주세요. 1:월 / 2:분기 / 3:반기 / 4:년 ")

    if cashflows_interval == "1":
        cashflows_interval_text = "month"
    elif cashflows_interval == "2":
        cashflows_interval_text = "quarter"
    elif cashflows_interval == "3":
        cashflows_interval_text = "half"
    else:
        cashflows_interval_text = "year"

    cashflows_amount = int(input("정기 입출금 설정액을 입력해주세요: "))
else:
    cashflows_interval_text = "X"
    cashflows_amount = 0

rebalancing = input("종목 비중 리밸런싱 여부를 알려주세요. [y/n] ")
if rebalancing == "y":
    rebalancing_interval = input("리밸런싱 주기를 선택해주세요. 1:월 / 2:분기 / 3:반기 / 4:년 ")
    while rebalancing_interval not in ["1", "2", "3", "4"]:
        rebalancing_interval = input("리밸런싱 주기를 선택해주세요. 1:월 / 2:분기 / 3:반기 / 4:년 ")

    if rebalancing_interval == "1":
        rebalancing_interval_text = "month"
    elif rebalancing_interval == "2":
        rebalancing_interval_text = "quarter"
    elif rebalancing_interval == "3":
        rebalancing_interval_text = "half"
    else:
        rebalancing_interval_text = "year"
else:
    rebalancing_interval_text = "X"

if not os.path.exists('backtesting'):
    os.makedirs('backtesting')
portfolio_config = {"I_amount": [initial_amount], "CF_interval": [cashflows_interval_text], "CF_amount": [cashflows_amount], "Re_interval": [rebalancing_interval_text]}
portfolio_config_df = pd.DataFrame(portfolio_config)
portfolio_config_df = portfolio_config_df.T
portfolio_config_df.to_csv('backtesting/portfolio_config.csv', header=False, encoding='utf-8-sig')

subprocess.run(['python', 'backtesting_config.py'])
sys.exit()
