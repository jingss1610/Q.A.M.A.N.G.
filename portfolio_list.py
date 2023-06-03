import pandas as pd
import re
import os
import subprocess
import sys

print("")
print("※ 면 책 ※")
print("금융투자상품은 자산가격 변동, 환율 변동 등에 따라 투자원금의 손실이 발생할 수 있으며, 그 손실은 투자자에게 귀속됩니다.")
print("투자는 자신의 책임과 위험 부담에서 이루어지는 것이므로 사용자의 투자 결과에 대해 책임을 지지 않습니다.")
print("이 소프트웨어는 투자 결정의 근거로 사용하기 위한 것이 아니며, 완전하다고 가정해서는 안 됩니다.")
print("")

tickers = []
weights = []

folder_list = 'portfolio_list'
if not os.path.exists(folder_list):
    os.mkdir(folder_list)
else:
    files = os.listdir(folder_list)
    portfolio_files = [f for f in files if
                       f.startswith('portfolio_') and f.endswith('.csv') and f.split('_')[1].split('.')[0].isdigit()]

    def sort_by_number(filename):
        return int(filename.split('_')[1].split('.')[0])
    portfolio_files = sorted(portfolio_files, key=sort_by_number)

    if len(portfolio_files) > 0:
        choice = input("기존에 생성한 포트폴리오를 불러오시겠습니까? [y/n] ")
        if choice.lower() == 'y':
            for i, file in enumerate(sorted(portfolio_files, key=lambda f: int(f.split('_')[1].split('.')[0]))):
                file_number = file.split('_')[1].split('.')[0]
                print(f"{i + 1}: {file}")
            while True:
                file_number = input("불러올 포트폴리오의 번호를 입력하세요. ")
                if not file_number.isdigit() or int(file_number) < 1 or int(file_number) > len(portfolio_files):
                    print("유효한 번호를 입력하세요. ")
                else:
                    file_number = int(file_number)
                    break
            selected_portfolio = pd.read_csv(os.path.join(folder_list, portfolio_files[int(file_number) - 1]),
                                             dtype={'Ticker': str})
            tickers = selected_portfolio['Ticker'].tolist()
            weights = selected_portfolio['Weight'].tolist()

            portfolio_data = {'Ticker': tickers, 'Weight': weights}
            selected_portfolio_df = pd.DataFrame(portfolio_data)
            selected_portfolio_df = selected_portfolio_df.set_index('Ticker')
            selected_portfolio_df.to_csv(os.path.join(folder_list, "portfolio_selected.csv"), encoding='utf-8-sig')

            if len(tickers) > 0:
                subprocess.run(['python', 'portfolio_price.py'], shell=True)
                sys.exit()

def validate_weight_input(weight):
    try:
        weight = int(weight)
    except ValueError:
        print("비중은 0 초과 100 이하의 정수만 입력 가능합니다.")
        return None
    if weight <= 0 or weight > 100:
        print("비중은 0 초과 100 이하의 정수만 입력 가능합니다.")
        return None
    return weight

def is_weight_100(weight):
    while sum(weights) != 100:
        if sum(weights) > 100:
            print(f"입력된 구성 종목의 비중 총합이 {sum(weights) - 100}% 만큼 초과합니다.")
        else:
            print(f"입력된 구성 종목의 비중 총합이 {100 - sum(weights)}% 만큼 부족합니다.")
        ticker_modify = input("수정 또는 추가할 종목의 티커를 입력하세요: ")
        if not re.match(r'^\d{6}$|^[a-zA-Z]{1,6}$|^\d{4}$|[a-zA-Z]+-?krw|금', ticker_modify, flags=re.IGNORECASE):
            print(f"{ticker_modify}는 유효한 티커가 아닙니다.")
            continue
        if weight is None:
            continue
        if ticker_modify in tickers:
            index_ = tickers.index(ticker_modify)
            weights[index_] = int(input(f"비중{index_ + 1}: "))
            weight = validate_weight_input(weight)
        else:
            tickers.append(ticker_modify)
            weights.append(weight)

while True:
    if sum(weights) != 100:
        print("")
        print("※ 참 조 ※")
        print("티커 입력은 대소문자를 구분하지 않습니다.")
        print("암호화폐는 티커 뒤에 '-KRW'를 붙여주세요. 예)BTC-KRW")
        print("금은 '금' 이라고 입력하세요.(국내 금 시세 매매기준율로 원/g)")
        print("")
        ticker = input(f"티커{len(tickers) + 1}: ")
        if ticker in tickers:
            print("중복 입력된 티커입니다.")
            continue
        if not ticker:
            choice = input("입력을 종료하시겠습니까? [y/n] ")
            if choice.lower() == 'y':
                break
            elif choice.lower() == 'n':
                continue
            else:
                continue
        if not re.match(r'^\d{6}$|^[a-zA-Z]{1,6}$|^\d{4}$|[a-zA-Z]+-?krw|금', ticker, flags=re.IGNORECASE):
            print(f"{ticker}는 유효한 티커가 아닙니다.")
            continue

        while True:
            weight = input(f"비중{len(weights) + 1}: ")
            weight = validate_weight_input(weight)
            if weight is None:
                continue
            if sum(weights) + weight > 100:
                print("종목 비중의 총합이 100%를 초과하게 됩니다.")
                continue
            break

    if sum(weights) == 100:
        if len(tickers) == 1:
            choice = input("단일 종목 포트폴리오입니다. 입력을 종료하시겠습니까? [y/n] ")
        else:
            choice = input("종목 비중의 총합이 100%입니다. 입력을 종료하시겠습니까? [y/n] ")
        if choice.lower() == 'y':
            break
        elif choice.lower() == 'n':
            ticker_modify = input("수정할 종목의 티커를 입력하세요: ")
            if not re.match(r'^\d{6}$|^[a-zA-Z]{1,6}$|^\d{4}$|[a-zA-Z]+-?krw|금', ticker_modify, flags=re.IGNORECASE):
                print(f"{ticker_modify}는 유효한 티커가 아닙니다.")
                continue
            if ticker_modify in tickers:
                index_ = tickers.index(ticker_modify)
                weight = int(input(f"비중{index_ + 1}:"))
                weights[index_] = weight
                weight = validate_weight_input(weight)
                is_weight_100(weight)
                continue
            else:
                print("수정할 종목의 티커를 입력하세요: ")
                continue
        else:
            continue
    tickers.append(ticker)
    weights.append(weight)

portfolio_list = pd.DataFrame({'Ticker': [t.upper() for t in tickers], 'Weight': weights})
portfolio_list.set_index('Ticker', inplace=True)
file_number = 1
while True:
    file_name = f"portfolio_{file_number}.csv"
    file_path = os.path.join(folder_list, file_name)
    if not os.path.exists(file_path):
        break
    file_number += 1
portfolio_list.to_csv(file_path, encoding='utf-8-sig')
portfolio_list.to_csv(os.path.join(folder_list, "portfolio_selected.csv"), encoding='utf-8-sig')

subprocess.run(['python', 'portfolio_price.py'])
sys.exit()
