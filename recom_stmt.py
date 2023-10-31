import os
from pyfinviz.quote import Quote
import FinanceDataReader as fdr
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import sys
import subprocess

start = time.time()

# S&P 500 종목 리스트
sp500 = fdr.StockListing('S&P500')
sp500_df = pd.DataFrame(sp500)
sp500_df['Symbol'].replace({'BRKB': 'BRK-B', 'BFB': 'BF-B'}, inplace=True)
symbols = sp500_df['Symbol'].tolist()

# KOSPI 200 종목 리스트
symbols_ks200 = []
names_ks200 = []
for page in range(1, 21):
    url = f'https://finance.naver.com/sise/entryJongmok.naver?&page={page}'
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    for td in soup.find_all('td', {'class': 'ctg'}):
        symbol = td.a.get('href').split('=')[1]
        name = td.a.text
        symbols_ks200.append(symbol)
        names_ks200.append(name)
df_ks200 = pd.DataFrame({'Symbol': symbols_ks200, 'Name': names_ks200})

# 디렉토리가 없으면 생성
folder = 'recom_stmt'
if not os.path.exists(folder):
    os.mkdir(folder)

start = time.time()

downloaded_syms = []

# S&P 500 종목별 재무제표 다운로드
def download_statement_sp500(sym):
    try:
        quote = Quote(ticker=sym)
        sp500_income_df = quote.income_statement_df.transpose()
        sp500_balance_df = quote.balance_sheet_df.transpose()
        sp500_cash_df = quote.cash_flow_df.transpose()

        income_transpose_df = pd.DataFrame({
            'Accounts': sp500_income_df.index,
            'Value': sp500_income_df.iloc[:, 0].values,
            'Symbol': sym
        })
        balance_transpose_df = pd.DataFrame({
            'Accounts': sp500_balance_df.index,
            'Value': sp500_balance_df.iloc[:, 0].values,
            'Symbol': sym
        })
        cash_transpose_df = pd.DataFrame({
            'Accounts': sp500_cash_df.index,
            'Value': sp500_cash_df.iloc[:, 0].values,
            'Symbol': sym
        })

        income_filename = os.path.join(folder, f'{sym}_income_statement.csv')
        income_transpose_df.to_csv(income_filename, index=False, mode='wb')

        balance_filename = os.path.join(folder, f'{sym}_balance_sheet.csv')
        balance_transpose_df.to_csv(balance_filename, index=False, mode='wb')

        cash_filename = os.path.join(folder, f'{sym}_cash_flow.csv')
        cash_transpose_df.to_csv(cash_filename, index=False, mode='wb')

        downloaded_syms.append(sym)
        print(f'{sym} Financial Statements saved')
    except:
        print(f'Error occurred while processing {sym} Financial Statements')

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(download_statement_sp500, sym) for sym in symbols]
    for future in as_completed(futures):
        result = future.result()

# KOSPI 200 종목별 재무제표 다운로드
def download_statement_ks200(sym):
    try:
        url = f'https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{sym}'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        divSonikY = soup.find("div", {"id": "divSonikY"})
        divDaechaY = soup.find("div", {"id": "divDaechaY"})
        divCashY = soup.find("div", {"id": "divCashY"})

        for tag in soup.select('[style*="display:none"]'):
            tag['style'] = 'display:block'

        income_statement = pd.read_html(str(divSonikY), encoding='utf-8')[0].iloc[:, [0, 4]].dropna()
        balance_sheet = pd.read_html(str(divDaechaY), encoding='utf-8')[0].iloc[:, [0, 4]].dropna()
        cash_flow = pd.read_html(str(divCashY), encoding='utf-8')[0].iloc[:, [0, 4]].dropna()

        income_statement.iloc[:,0] = income_statement.iloc[:,0].apply(lambda x: x.replace("계산에 참여한 계정 펼치기", "")
        if "계산에 참여한 계정 펼치기" in x else x)
        balance_sheet.iloc[:,0] = balance_sheet.iloc[:,0].apply(lambda x: x.replace("계산에 참여한 계정 펼치기", "")
        if "계산에 참여한 계정 펼치기" in x else x)
        cash_flow.iloc[:,0] = cash_flow.iloc[:,0].apply(lambda x: x.replace("계산에 참여한 계정 펼치기", "")
        if "계산에 참여한 계정 펼치기" in x else x)

        ks200_income_df = pd.DataFrame({
            'Accounts': income_statement.iloc[:, 0].values,
            'Value': income_statement.iloc[:, 1].values,
            'Symbol': sym
        })

        ks200_balance_df = pd.DataFrame({
            'Accounts': balance_sheet.iloc[:, 0].values,
            'Value': balance_sheet.iloc[:, 1].values,
            'Symbol': sym
        })

        ks200_cash_df = pd.DataFrame({
            'Accounts': cash_flow.iloc[:, 0].values,
            'Value': cash_flow.iloc[:, 1].values,
            'Symbol': sym
        })

        account_counts = defaultdict(int)
        def process_accounts(df):
            for i in range(len(df)):
                account = df.iloc[i]['Accounts']
                if account_counts[account] == 0:
                    account_counts[account] += 1
                else:
                    df.at[i, 'Accounts'] = account + str(account_counts[account])
                    account_counts[account] += 1
            return df

        ks200_income_df = process_accounts(ks200_income_df)
        ks200_balance_df = process_accounts(ks200_balance_df)
        ks200_cash_df = process_accounts(ks200_cash_df)

        ks200_income_df.to_csv(f"{folder}/{sym}_income_statement.csv", index=False, encoding='utf-8-sig')
        ks200_balance_df.to_csv(f"{folder}/{sym}_balance_sheet.csv", index=False, encoding='utf-8-sig')
        ks200_cash_df.to_csv(f"{folder}/{sym}_cash_flow.csv", index=False, encoding='utf-8-sig')

        downloaded_syms.append(sym)
        print(f'{sym} Financial Statements saved')
    except:
        print(f'Error occurred while processing {sym} Financial Statements')

with ThreadPoolExecutor() as executor:
    futures = [executor.submit(download_statement_ks200, sym) for sym in df_ks200['Symbol']]
    for future in as_completed(futures):
        result = future.result()

# 종목별 Financial Statement 불러오기
dfs = {}
for sym in downloaded_syms:
    dfs[sym] = {}
    for fs_type in ['income_statement', 'balance_sheet', 'cash_flow']:
        csv_fn = os.path.join(folder, f'{sym}_{fs_type}.csv')
        try:
            df = pd.read_csv(csv_fn, parse_dates=True, index_col='Accounts', encoding='utf-8-sig')
            df = df[['Value']]
            dfs[sym][fs_type] = df
            df.columns = [sym]
        except Exception as e:
            print(e)

# 종목별 Financial Statement 병합
df_income = pd.concat([dfs[sym]['income_statement'] for sym in downloaded_syms], axis=1)
df_balance = pd.concat([dfs[sym]['balance_sheet'] for sym in downloaded_syms], axis=1)
df_cash = pd.concat([dfs[sym]['cash_flow'] for sym in downloaded_syms], axis=1)

# 열 이름을 알파벳 순으로 정렬
df_income = df_income.reindex(sorted(df_income.columns), axis=1)
df_balance = df_balance.reindex(sorted(df_balance.columns), axis=1)
df_cash = df_cash.reindex(sorted(df_cash.columns), axis=1)

# 모든 종목의 Financial Statement를 csv 파일로 저장
all_stock_income_csv = os.path.join(folder, 'all_stock_income.csv')
df_income.to_csv(all_stock_income_csv, index=True, header=True, encoding='utf-8-sig', mode='wb')
print(f"All stock income statement saved to {all_stock_income_csv}")

all_stock_balance_csv = os.path.join(folder, 'all_stock_balance.csv')
df_balance.to_csv(all_stock_balance_csv, index=True, header=True, encoding='utf-8-sig', mode='wb')
print(f"All stock balance sheet saved to {all_stock_balance_csv}")

all_stock_cash_csv = os.path.join(folder, 'all_stock_cash.csv')
df_cash.to_csv(all_stock_cash_csv, index=True, header=True, encoding='utf-8-sig', mode='wb')
print(f"All stock cash flow saved to {all_stock_cash_csv}")

end = time.time()
print(f"Elapsed time: {end - start} seconds")

subprocess.run(['python', 'recommending.py'])
sys.exit()
