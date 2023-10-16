import os
import csv
import finviz
import FinanceDataReader as fdr
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
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

# KOSPI 200 종목 Sector 분류(딕셔너리)
sector_list = {'Basic Materials': ['화학', '건축소재', '용기 및 포장', '금속 및 광물', '종이 및 목재'],
               'Communication Services': ['유선통신', '무선통신'],
               'Consumer Cyclical': ['자동차부품', '자동차', '내구소비재', '레저용품', '섬유 및 의복', '호텔 및 레저', '교육', '미디어',
                                     '도소매', '온라인쇼핑', '백화점'],
               'Consumer Defensive': ['음료', '식료품', '담배', '가정생활용품', '개인생활용품'],
               'Energy': ['에너지 시설 및 서비스', '석유 및 가스'],
               'Financial': ['상업은행', '상호저축은행', '창업투자 및 종금', '소비자 금융', '보험', '증권'],
               'Healthcare': ['의료장비 및 서비스', '바이오', '제약'],
               'Industrials': ['건축자재', '건설', '전기장비', '복합 산업', '기계', '무역', '조선', '상업서비스', '항공운수', '해상운수',
                               '육상운수', '운송인프라'],
               'Real Estate': ['부동산'],
               'Technology': ['인터넷 서비스', 'IT 서비스', '일반 소프트웨어', '게임 소프트웨어', '통신장비', '휴대폰 및 관련부품',
                              '셋톱 박스', '컴퓨터 및 주변기기', '전자 장비 및 기기', '보안장비', '사무기기', '반도체 및 관련장비',
                              '디스플레이 및 관련부품'],
               'Utilities': ['전력', '가스']}

# 디렉토리가 없으면 생성
folder = 'recom_funda'
if not os.path.exists('recom_funda'):
    os.mkdir('recom_funda')

# S&P 500 종목별 펀더멘털 데이터 다운로드
downloaded_syms = []
for sym in symbols:
    try:
        csvFile = open(f"recom_funda/{sym}.csv", mode='w', newline='')
        writer = csv.writer(csvFile)

        stock_data = finviz.get_stock(sym)

        writer.writerow(('Indicators', 'Value', 'Symbol'))

        data_order = ['Company', 'Sector', 'Market Cap', 'Income', 'Sales', 'Dividend', 'Dividend %', 'P/E', 'PEG', 'P/S',
                      'P/B', 'Quick Ratio', 'Current Ratio', 'Debt/Eq', 'EPS (ttm)', 'ROA', 'ROE', 'ROI', 'Gross Margin',
                      'Oper. Margin', 'Profit Margin', 'Payout', 'Shs Outstand', 'Beta']

        for name in data_order:
            if name in stock_data.keys():
                writer.writerow((name, stock_data[name], sym))

        csvFile.close()
        downloaded_syms.append(sym)
        print(f"{sym} saved")

    except Exception as e:
        print(f"Error occurred while processing {sym}: {str(e)}")
        continue

# KOSPI 200 종목별 펀더멘털 데이터 다운로드
def download_data(sym):
    try:
        url = f'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A{sym}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        table1 = soup.find('table', {'class': 'us_table_ty1 table-hb thbg_g h_fix zigbg_no'})
        rows1 = table1.find_all('tr')
        rows2 = [cell.find_all(['th', 'td']) for cell in soup.select('.um_col2wrap.upTabDiv table.us_table_ty1.h_fix tr')]

        data = [[cell[0].text.strip(), cell[1].text.strip().replace(',', '')] for cell in rows2]
        for row in rows1:
            if len(row) > 2:
                data += [[row.find_all(['th', 'td'])[0].text.strip(),
                          row.find_all(['th', 'td'])[1].text.strip().replace(',', '')],
                         [row.find_all(['th', 'td'])[2].text.strip(),
                          row.find_all(['th', 'td'])[3].text.strip().replace(',', '')]]
            else:
                data.append([cell.text.strip() if idx != 1 else cell.text.strip().replace(',', '') for idx, cell in
                             enumerate(row.find_all(['th', 'td']))])
        sectors = [sector.text.strip('FICS  ').replace(u'\xa0', u' ') for sector in soup.select("div>p>span.stxt")[1]]
        for sector in sectors:
            for key, value in sector_list.items():
                if sector in value:
                    data.append(["Sector", key])

        urls = [
            (f'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{sym}', [0, 4]),
            (f'http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&gicode=A{sym}', [0, 5]),
            (f'http://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&gicode=A{sym}', [0, 5])
        ]

        for url, columns in urls:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            table_wrap = soup.find('div', {'class': 'ul_col2wrap pd_t25'})
            table = table_wrap.find('table', {'class': 'us_table_ty1 h_fix zigbg_no'})
            rows = table.find_all('tr')
            data += [[cell.text.strip().replace(',', '') for idx, cell in enumerate(row.find_all(['th', 'td'])) if
                      idx in columns] for row in rows]

        df = pd.DataFrame(data, columns=['Indicators', 'Value'])
        df['Indicators'] = df['Indicators'].str[:6]

        try:
            peg_value = float(df.loc[df['Indicators'] == 'PER수정주']['Value'].iloc[0].replace(',', '')) / float(
                df.loc[df['Indicators'] == 'EPS증가율']['Value'].iloc[0].replace(',', ''))
        except ValueError:
            peg_value = ''
        df = pd.concat([df, pd.DataFrame({'Indicators': 'PEG', 'Value': peg_value}, index=[0])], ignore_index=True)

        try:
            net_profit_margin_value = float(
                df.loc[df['Indicators'] == '당기순이익']['Value'].iloc[0].replace(',', '')) / float(
                df.loc[df['Indicators'] == '매출액']['Value'].iloc[0].replace(',', '')) * 100
        except ValueError:
            net_profit_margin_value = ''
        df = pd.concat(
            [df, pd.DataFrame({'Indicators': 'Profit Margin', 'Value': net_profit_margin_value}, index=[0])],
            ignore_index=True)

        df.loc[df['Indicators'] == '부채비율(총', 'Value'] = df.loc[df['Indicators'] == '부채비율(총', 'Value'].apply(
            lambda x: round(float(x) / 100, 2) if x != '' else x)

        df['Indicators'] = df['Indicators'].replace(
            {'구분': 'Company', '시가총액': 'Market Cap', '영업이익': 'Income', '매출액': 'Sales', 'DPS(보통': 'Dividend',
             '배당수익률': 'Dividend %', 'PER수정주': 'P/E', 'PSR수정주': 'P/S', 'PBR수정주': 'P/B', '당좌비율(당': 'Quick Ratio',
             '유동비율(유': 'Current Ratio', '부채비율(총': 'Debt/Eq', 'EPS(원)': 'EPS (ttm)', 'ROA(당기': 'ROA', 'ROE(지배': 'ROE',
             'ROIC(세': 'ROI', '매출총이익율': 'Gross Margin', '영업이익률(': 'Oper. Margin', '배당성향(현': 'Payout',
             '유동주식수/': 'Shs Outstand', '베타(1년)': 'Beta'})

        indices_to_keep = ['Company', 'Sector', 'Market Cap', 'Income', 'Sales', 'Dividend', 'Dividend %', 'P/E', 'PEG',
                           'P/S', 'P/B', 'Quick Ratio', 'Current Ratio', 'Debt/Eq', 'EPS (ttm)', 'ROA', 'ROE', 'ROI',
                           'Gross Margin', 'Oper. Margin', 'Profit Margin', 'Payout', 'Shs Outstand', 'Beta']
        df = df.loc[df['Indicators'].isin(indices_to_keep)]
        df = df.drop_duplicates(subset=['Indicators'])
        df.loc[df['Indicators'] == 'Shs Outstand', 'Value'] = df.loc[df['Indicators'] == 'Shs Outstand', 'Value'].str.split(' /').str[0]

        file_path = os.path.join(folder, f'{sym}.csv')
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        downloaded_syms.append(sym)
        print(f"{sym} saved")

    except Exception as e:
        print(f"Error occurred while processing {sym}: {str(e)}")
        pass

with ThreadPoolExecutor() as executor:
    executor.map(download_data, df_ks200['Symbol'])

# 종목별 펀더멘털 데이터 불러오기
dfs = []
for sym in downloaded_syms:
    csv_fn = os.path.join(folder, f'{sym}.csv')
    try:
        df = pd.read_csv(csv_fn, parse_dates=True, index_col='Indicators')
        df = df[['Value']]
        df['Value'] = df['Value'].replace('-', '')
        df['Value'] = df['Value'].str.replace('%', '', regex=True)
        dfs.append(df)
        df.columns = [sym]
    except Exception as e:
        print(e)

# 종목별 펀더멘털 데이터 병합
df_funda = pd.concat(dfs, axis=1)

# 열 이름을 알파벳 순으로 정렬
df_funda = df_funda.reindex(sorted(df_funda.columns), axis=1)

# 모든 종목의 펀더멘털 데이터를 CSV 파일로 저장
all_stock_funda_indicators_csv = os.path.join(folder, 'all_stock_funda_indicators.csv')
df_funda.to_csv(all_stock_funda_indicators_csv, index=True, header=True, encoding='utf-8-sig', mode='w')
print(f"All stock fundamental indicators saved to {all_stock_funda_indicators_csv}")

end = time.time()
print(f"Elapsed time: {end - start} seconds")

subprocess.run(['python', 'recommending.py'])
sys.exit()
