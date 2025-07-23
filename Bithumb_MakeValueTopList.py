#-*-coding:utf-8 -*-
'''

필요하다면 line_alert을 활용해 메시지를 오게 하는 것도 좋은 커스텀 방향입니다!

(crontab 예시)
40 14 * * * python3 /var/autobot/Bithumb_MakeValueTopList.py

오류(버그)를 만난다면
검색이나 챗GPT등에 먼저 에러 로그를 
복사&붙여넣기로 알아 본 뒤 그래도 모르겠다면
댓글로 알려주세요 :)

게만아 파이썬 자동매매 수익 & 수강 후기
https://blog.naver.com/zacra/223568483228


'''
import myBithumb   #우리가 만든 함수들이 들어있는 모듈
import json
import time
import pandas as pd
from datetime import datetime



# 설정값
TIME_PERIOD = "1d"  # X봉 기준  1d,4h,1h,30m,15m,10m,5m,3m,1m
TOP_NUM = 10        # 상위 N개

########################################################
MAKE_EXEL = True #서버에 업로드해서 실전 운용시에는 False로 바꾸고 업로드 추천!
########################################################

# 결과 파일 경로
json_file_path = f"./Bithumb_{TIME_PERIOD}_Top{TOP_NUM}ValueCoinList.json"
excel_file_path = f"./Bithumb_{TIME_PERIOD}_Top{TOP_NUM}ValueCoinList.xlsx"

# 모든 코인 심볼 가져오기
Tickers = myBithumb.GetTickers()
time.sleep(0.1)


########################################################
#영상에 없지만 상폐 당할 수 있는 유의 코인은 제외 하기 위해 리스트로 가져오기
CautionCoinList = myBithumb.Get_CAUTION_Tickers()
########################################################




# 거래대금 계산을 위한 딕셔너리
dic_coin_value = dict()

for ticker in Tickers:
    print("--------------------------", ticker)
    
    if ticker in CautionCoinList:
        print(f"{ticker}: 유의 코인입니다. 제외합니다.")
        continue
    
    try:
        time.sleep(0.1)
        df = myBithumb.GetOhlcv(ticker, TIME_PERIOD, 200)
        
        # 데이터가 충분한지 확인
        if len(df) < 1:  # 최소 1개의 데이터가 필요
            print(f"{ticker}: 데이터가 부족합니다. (현재: {len(df)}개, 필요: 1개)")
            continue
        

        # 거래대금 계산
        current_value = float(df['value'].iloc[-1])  # 가장 최근 거래대금
        
        dic_coin_value[ticker] = current_value
        print(f"{ticker}: 거래대금 {current_value:,.0f}")

    except Exception as e:
        print(f"---: {e}")

# 거래대금 기준으로 정렬 (내림차순)
dic_sorted_coin_value = sorted(dic_coin_value.items(), key=lambda x: x[1], reverse=True)

# 상위 N개 코인 리스트 생성
TopCoinList = list()
TopCoinValues = list()  # 거래대금 저장용 리스트
for i, coin_data in enumerate(dic_sorted_coin_value):
    if i < TOP_NUM:
        TopCoinList.append(coin_data[0])
        TopCoinValues.append(coin_data[1])
    else:
        break

print("--------------------------------")
print(f"거래대금 기준 상위 {TOP_NUM}개 코인:")
print(TopCoinList)
print("--------------------------------")

# JSON 파일에 리스트를 저장합니다
with open(json_file_path, 'w') as outfile:
    json.dump(TopCoinList, outfile)


if MAKE_EXEL == True:
    # 엑셀 파일로 저장하기 위한 데이터프레임 생성
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame({
        '코인 심볼': TopCoinList,
        '거래대금': TopCoinValues,
        '순위': range(1, len(TopCoinList) + 1),
        '기준 시간': [current_time] * len(TopCoinList),
        '기준 기간': [TIME_PERIOD] * len(TopCoinList)
    })

    # 엑셀 파일로 저장
    df.to_excel(excel_file_path, index=False, sheet_name='거래대금 상위 코인')
    print(f"데이터가 {json_file_path}와 {excel_file_path}에 저장되었습니다.")

else:
    print(f"데이터가 {json_file_path}에 저장되었습니다.")
