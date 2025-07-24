#-*-coding:utf-8 -*-
'''

투자하고자 하는 코인을 이미 가지고 있다면
모두 매도하고 시작해야 비중이 제대로 적용된다는 점 참고하세요 :)


(crontab 예시)
0 15 * * * python3 /var/autobot/Bithumb_BB_Bot.py

오류(버그)를 만난다면
검색이나 챗GPT등에 먼저 에러 로그를 
복사&붙여넣기로 알아 본 뒤 그래도 모르겠다면
댓글로 알려주세요 :)

게만아 파이썬 자동매매 수익 & 수강 후기
https://blog.naver.com/zacra/223568483228

!! 클래스에서 다운로드한 유료 코드를 공개 및 공유하는 행위는 하시면 안되용 :) !!

'''
import myBithumb
import pandas as pd
import time
import json
import line_alert
import pprint
import GMA_Candle

def get_coin_list():
        #투자할 종목!
    # 아래는 기존 고정 리스트를 대체합니다.
    # 1. 각 기준별 TopCoinList를 직접 생성
    # 2. 세 리스트의 교집합을 구해 InvestCoinList로 할당
    print("--------------------------------")
    print("TopCoinList 생성중")
    print("--------------------------------")

    # === 1. 거래대금 기준 TopCoinList (상위 20개) ===
    TOP_NUM_VALUE = 30
    TOP_NUM_MA = 20
    TOP_NUM_UPRATE = 10
    Tickers = myBithumb.GetTickers()
    time.sleep(0.1)
    CautionCoinList = []#myBithumb.Get_CAUTION_Tickers()
    TIME_PERIOD = "1h"

    # 거래대금 상위 30개 (최근 24시간 합산)
    dic_coin_value = dict()
    for ticker in Tickers:
        if ticker in CautionCoinList:
            continue
        try:
            time.sleep(0.1)
            df = myBithumb.GetOhlcv(ticker, TIME_PERIOD, 24)
            if len(df) < 1:
                print(f"{ticker} has no data")
                continue
            # 최근 24시간 거래대금 합산
            if len(df) >= 24:
                value_24h = float(df['value'].iloc[-24:].sum())
            else:
                value_24h = float(df['value'].sum())
            dic_coin_value[ticker] = value_24h
        except Exception as e:
            print(f"Error for {ticker}: {e}")
            continue
    dic_sorted_coin_value = sorted(dic_coin_value.items(), key=lambda x: x[1], reverse=True)
    TopCoinList_Value = [coin_data[0] for i, coin_data in enumerate(dic_sorted_coin_value) if i < TOP_NUM_VALUE]
    print('거래대금 상위:', TopCoinList_Value)

    # === 2. MA 기준 TopCoinList (상위 30개, 거래대금 상위 60개 내에서만) ===
    MA_PERIOD = 60
    dic_ma_above = dict()
    for ticker in TopCoinList_Value:
        try:
            time.sleep(0.1)
            df = myBithumb.GetOhlcv(ticker, TIME_PERIOD, MA_PERIOD + 10)
            if len(df) < MA_PERIOD + 2:
                continue
            df['MA'] = df['close'].rolling(window=MA_PERIOD).mean()
            prev_price = float(df['close'].iloc[-1])
            prev_ma = float(df['MA'].iloc[-1])
            is_above_ma = prev_price > prev_ma
            if is_above_ma:
                disparity = (prev_price / prev_ma) * 100
                dic_ma_above[ticker] = disparity
        except Exception:
            continue
    dic_sorted_ma_above = sorted(dic_ma_above.items(), key=lambda x: x[1], reverse=True)
    TopCoinList_MA = [coin_data[0] for i, coin_data in enumerate(dic_sorted_ma_above) if i < TOP_NUM_MA]
    print('MA 상위:', TopCoinList_MA)

    # === 3. 등락률 기준 TopCoinList (상위 15개, 위 30개 내에서만) ===
    MIN_RATE = 1.5
    dic_coin_rate = dict()
    for ticker in TopCoinList_MA:
        try:
            time.sleep(0.1)
            df = myBithumb.GetOhlcv(ticker, TIME_PERIOD, 5)
            if len(df) < 4:
                continue
            close = df['close']
            rate1 = abs((float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100)
            rate2 = abs((float(close.iloc[-2]) - float(close.iloc[-3])) / float(close.iloc[-3]) * 100)
            rate3 = abs((float(close.iloc[-3]) - float(close.iloc[-4])) / float(close.iloc[-4]) * 100)
            sum_rate = rate1 + rate2 + rate3
            dic_coin_rate[ticker] = sum_rate
        except Exception:
            continue
    dic_sorted_coin_rate = sorted(dic_coin_rate.items(), key=lambda x: x[1], reverse=True)
    TopCoinList_UpRate = []
    cnt = 0
    for coin_data in dic_sorted_coin_rate:
        if coin_data[1] >= MIN_RATE:
            cnt += 1
            if cnt <= TOP_NUM_UPRATE:
                TopCoinList_UpRate.append(coin_data[0])
            else:
                break
    print('등락률 상위:', TopCoinList_UpRate)

    InvestCoinList = TopCoinList_UpRate
    print('최종 투자 대상:', InvestCoinList)
    return InvestCoinList


def Bithumb_BB_Bot():
    #시간 정보를 읽는다
    time_info = time.gmtime()

    hour_n = time_info.tm_hour
    min_n = time_info.tm_min

    print("hour_n:", hour_n) #참고용    
    print("min_n:", min_n) #참고용   

    day_str = str(time_info.tm_year) + str(time_info.tm_mon) + str(time_info.tm_mday)

    print("day_str:",day_str) #참고용   


    #최소 매수 금액
    minimunMoney = 5500



    #내가 가진 잔고 데이터를 다 가져온다.
    balances = myBithumb.GetBalances()

    #TotalMoney = myBithumb.GetTotalMoney(balances) #총 원금

    #내 평가금에서 투자하고 싶으면 아래 코드
    TotalMoney = myBithumb.GetTotalRealMoney(balances) 

    #내 남은 원화(현금)
    RemainCash = myBithumb.GetCoinAmount(balances,"KRW")

    ######################################################
    #이런식으로 해당 전략에 할당할 금액을 조절
    InvestMoney = TotalMoney * 0.10 #30% 투자 적절히 수정!
    ######################################################

    InvestCoinList = get_coin_list()

    # === 투자 대상이 아닌 코인 전량 매도 ===
    strategy_info_file_path = "./Bithumb_BB_Bot_Info.json" 
    StrategyInfoList = []  # 반드시 빈 리스트로 초기화
    try:
        with open(strategy_info_file_path, 'r') as json_file:
            StrategyInfoList = json.load(json_file)
    except Exception as e:
        # 파일이 없거나 읽기 실패 시에도 빈 리스트로 유지
        print("Exception by First or file read error", e)

    for info in balances:
        coin = info['currency']
        if coin == 'KRW':
            continue
        try:
            amount = float(info['balance'])
        except Exception:
            continue
        market_id = f"KRW-{coin}"
        # 현재가 조회 (5천원 이하 코인 제외용)
        try:
            df = myBithumb.GetOhlcv(market_id, "1h", 1)
            current_price = float(df['close'].iloc[-1])
        except Exception:
            continue
        if amount * current_price < 5000:
            continue
        if amount > 0 and market_id not in InvestCoinList:
            print(f"{market_id} 전량 매도: {amount}")
            try:
                myBithumb.SellCoinMarket(market_id, amount)
                msg = f"{market_id}는 투자대상에서 제외되어 전량({amount}) 매도했습니다."
                print(msg)
                line_alert.SendMessage(msg)
                StrategyInfoList = [item for item in StrategyInfoList if item.get('ticker') != market_id]
                with open(strategy_info_file_path, 'w') as outfile:
                    json.dump(StrategyInfoList, outfile)
            except Exception as e:
                print(f"{market_id} 매도 실패: {e}")

    # === 보유 코인 중 수익률 -8% 이하(손실 8% 이상)면 전량 매도, 20%/32% 익절 ===
    for info in balances:
        coin = info['currency']
        if coin == 'KRW':
            continue
        try:
            amount = float(info['balance'])
        except Exception:
            continue
        market_id = f"KRW-{coin}"
        # 현재가 조회 (5천원 이하 코인 제외용)
        try:
            df = myBithumb.GetOhlcv(market_id, "1h", 1)
            current_price = float(df['close'].iloc[-1])
        except Exception:
            continue
        if amount * current_price < 5000:
            continue
        if amount > 0:
            # 평균 매입가를 함수로 얻기
            avg_buy_price = myBithumb.GetAvgBuyPrice(balances, market_id)
            if avg_buy_price == 0:
                continue
            # 수익률 계산
            profit_rate = (current_price - avg_buy_price) / avg_buy_price * 100

            # StrategyInfoList에서 해당 코인 정보 찾기 (익절 기록용)
            PickCoinInfo = None
            for CoinInfo in StrategyInfoList:
                if CoinInfo.get('ticker') == market_id:
                    PickCoinInfo = CoinInfo
                    break

            # === 32% 초과: 전량 익절 ===
            if profit_rate > 32.0:
                print(f"{market_id} 수익률 {profit_rate:.2f}%로 32% 초과, 전량 익절: {amount}")
                try:
                    myBithumb.SellCoinMarket(market_id, amount)
                    msg = f"{market_id}는 수익률 {profit_rate:.2f}%로 32% 초과라 전량({amount}) 익절했습니다."
                    print(msg)
                    line_alert.SendMessage(msg)
                    # StrategyInfoList에서 해당 코인 정보 삭제
                    StrategyInfoList = [item for item in StrategyInfoList if item.get('ticker') != market_id]
                    with open(strategy_info_file_path, 'w') as outfile:
                        json.dump(StrategyInfoList, outfile)
                except Exception as e:
                    print(f"{market_id} 매도 실패: {e}")
                continue  # 이미 전량 익절했으니 다음 코인으로

            # === 20% 초과: 50% 익절(한 번만) ===
            if profit_rate > 20.0 and PickCoinInfo is not None:
                if not PickCoinInfo.get('TakeProfit20', False):
                    sell_amount = amount * 0.5
                    print(f"{market_id} 수익률 {profit_rate:.2f}%로 20% 초과, 50% 익절: {sell_amount}")
                    try:
                        myBithumb.SellCoinMarket(market_id, sell_amount)
                        msg = f"{market_id}는 수익률 {profit_rate:.2f}%로 20% 초과라 50%({sell_amount}) 익절했습니다."
                        print(msg)
                        line_alert.SendMessage(msg)
                        # 익절 기록
                        PickCoinInfo['TakeProfit20'] = True
                        with open(strategy_info_file_path, 'w') as outfile:
                            json.dump(StrategyInfoList, outfile)
                    except Exception as e:
                        print(f"{market_id} 매도 실패: {e}")

            # === -8% 이하: 전량 손절 ===
            if profit_rate <= -8.0:
                print(f"{market_id} 수익률 {profit_rate:.2f}%로 -8% 이하, 전량 매도: {amount}")
                try:
                    myBithumb.SellCoinMarket(market_id, amount)
                    msg = f"{market_id}는 수익률 {profit_rate:.2f}%로 -8% 이하라 전량({amount}) 매도했습니다."
                    print(msg)
                    line_alert.SendMessage(msg)
                    # StrategyInfoList에서 해당 코인 정보 삭제
                    StrategyInfoList = [item for item in StrategyInfoList if item.get('ticker') != market_id]
                    with open(strategy_info_file_path, 'w') as outfile:
                        json.dump(StrategyInfoList, outfile)
                except Exception as e:
                    print(f"{market_id} 매도 실패: {e}")

    CoinMoney = InvestMoney / len(InvestCoinList) #코인당 할당 금액

    #분할된 투자금!
    StMoney = CoinMoney / 10.0 #10분할!

    FixMoneyRate = 0.0 #10분할 중 2개를 항상 가져가는 비중으로 설정
    TrendMoneyRate = 3 #10분할 중 2개를 추세에 따라 정의
    DantaMoneyRate = 7 #10분할 중 6개를 단타로 활용 

    print("StMoney:", str(format(round(StMoney), ',')))

    #단타시 최소 수익 기준 수익률!
    DANTA_TARGET_REVENUE = 0.015 #1.5% 



    ##############################################################################
    #전략이 매수한 코인 리스트
    StrategyInfoList = list()

    #파일 경로입니다.
    strategy_info_file_path = "./Bithumb_BB_Bot_Info.json" 

    try:
        #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
        with open(strategy_info_file_path, 'r') as json_file:
            StrategyInfoList = json.load(json_file)

    except Exception as e:
        #처음에는 파일이 존재하지 않으면 예외처리가 됩니다!
        print("Exception by First")

    ##############################################################################


    #HMR전략에서 활용하는 최적 이평선 정보를 파일을 읽어온다!
    CoinFindMaList = list()

    #파일 경로입니다.
    coinfindma_file_path = "./Bithumb_MakeBestMaForHighMaRsi.json" 

    try:
        #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
        with open(coinfindma_file_path, 'r') as json_file:
            CoinFindMaList = json.load(json_file)

    except Exception as e:
        print("Exception: ", e)



    #투자할 종목을 순회한다!
    for ticker in InvestCoinList:

        print("ticker:", ticker)


        #종목 데이터
        PickCoinInfo = None

        #저장된 종목 데이터를 찾는다
        for CoinInfo in StrategyInfoList:
            if CoinInfo['ticker'] == ticker:
                PickCoinInfo = CoinInfo
                break

        #PickCoinInfo 이게 없다면 매수되지 않은 처음 상태이거나 이전에 손으로 매수한 종목인데 해당 봇으로 돌리고자 할 때!
        if PickCoinInfo == None:

            InfinityDataDict = dict()
            
            InfinityDataDict['ticker'] = ticker #종목 코드
            InfinityDataDict['DateStrForToday'] = '0' #하루에 한번 체크하고 매수등의 처리를 하기 위한 값
            InfinityDataDict['InitFixVolume'] = 0  #초기 고정비중 매수 수량
            InfinityDataDict['BuyTrendOK'] = False  #추세가 확인되어 매수했는지 여부!
            InfinityDataDict['BuyTrendVolume'] = 0  #추세가 확인되어 매수한 수량!
            
            
            #단타칠때 진입지점을 기록할 리스트 DantaMoneyRate 만큼 개수를 미리 생성!
            DantaList = list()
            for i in range(0,int(DantaMoneyRate)): 
                DataDataDict = dict()
                DataDataDict['Id'] = i+1 #아이디
                DataDataDict['EntryPrice'] = 0 #진입가격
                DataDataDict['DantaAmt'] = 0   #단타 수량
                DataDataDict['IsBuy'] = False    #매수 상태인지 여부
                DantaList.append(DataDataDict)

            InfinityDataDict['DantaList'] = DantaList


            StrategyInfoList.append(InfinityDataDict) #데이터를 추가 한다!


            msg = ticker + " 별은 봇 첫 시작!!!!"
            print(msg) 
            line_alert.SendMessage(msg) 


            PickCoinInfo = InfinityDataDict
            #파일에 저장
            with open(strategy_info_file_path, 'w') as outfile:
                json.dump(StrategyInfoList, outfile)
                



        delay = '1h'
        #if PickCoinInfo['DateStrForToday'] != day_str: #오늘 매매 내역이 없다면
        if True:

            #캔들 데이터를 읽는다
            df = myBithumb.GetOhlcv(ticker,delay,200)

            #현재가
            CurrentPrice = float(df['close'].iloc[-1])




            #########################################################
            #########################################################
            #########################################################
            # 무조건 보유하는 비중 만큼 코인 매수

            #투자평가금의 FixMoneyRate는 무조건 보유해야 하니깐 이보다 작을 경우에만 추가매수 합니다!
            LongTermFixMoney = StMoney * FixMoneyRate

            CoinFixNowMoney = PickCoinInfo['InitFixVolume'] * CurrentPrice


            #장기 보유할 금액비중이 현재 코인 평가금보다 크다면!!
            if LongTermFixMoney > CoinFixNowMoney:

                GapMoney = LongTermFixMoney - CoinFixNowMoney


                if GapMoney >= minimunMoney:

                    #시장가 주문을 넣는다!
                    balances = myBithumb.BuyCoinMarket(ticker,GapMoney)
                    
                    PickCoinInfo['InitFixVolume'] += (GapMoney / CurrentPrice)

                    msg = ticker + " 별은 봇 " + str(FixMoneyRate*10) + "% 비중이 안차서 " + str(GapMoney)+ "원어치 매수 했어요!"
                    print(msg)  
                    line_alert.SendMessage(msg) 




            #########################################################
            #########################################################
            #########################################################


            small_ma = 10
            big_ma = 60

            for maData in CoinFindMaList:
                if maData['coin_ticker'] == ticker:
                    #pprint.pprint(maData)
                    if maData['RevenueRate'] > 0: #수익률이 0보다 클 때만 (대부분의 경우에는 0보다 크다)
                        small_ma,big_ma = maData['ma_str'].split()
                    break

            ########################################
            # 이동평균선 계산
            df['small_ma'] = df['high'].rolling(int(small_ma)).mean()    # 단기 고가 이동평균
            df['big_ma'] = df['high'].rolling(int(big_ma)).mean()        # 장기 고가 이동평균
            ########################################

            IsUpTrend = False #상승 추세여부
            IsDownTrend = False #하락 추세여부

            if (df['small_ma'].iloc[-3] <= df['small_ma'].iloc[-2] or df['small_ma'].iloc[-2] <= df['close'].iloc[-2]) and (df['big_ma'].iloc[-3] <= df['big_ma'].iloc[-2] and df['big_ma'].iloc[-2] <= df['close'].iloc[-2]):
                IsUpTrend = True

            if (df['small_ma'].iloc[-3] > df['small_ma'].iloc[-2] and df['small_ma'].iloc[-2] > df['close'].iloc[-2]) and (df['big_ma'].iloc[-3] > df['big_ma'].iloc[-2] or df['big_ma'].iloc[-2] > df['close'].iloc[-2]):
                IsDownTrend = True



            #투자평가금의 TrendMoneyRate 만큼을 추세에 따라 보유한다.
            LongTermTrendMoney = StMoney * TrendMoneyRate



            #아직 추세 비중 매수하지 않았는데 상승추세다!
            if PickCoinInfo['BuyTrendOK'] == False and IsUpTrend == True:

                #시장가 주문을 넣는다!
                balances = myBithumb.BuyCoinMarket(ticker,LongTermTrendMoney)

                PickCoinInfo['BuyTrendVolume'] = LongTermTrendMoney / CurrentPrice
                PickCoinInfo['BuyTrendOK'] = True

                msg = ticker + " 별은 봇 상승 추세가 확인되어 " + str(TrendMoneyRate*10) + "% 비중 " + str(LongTermTrendMoney)+ "원어치 매수 했어요!"
                print(msg)  
                line_alert.SendMessage(msg) 

            else:

                #이미 추세 비중 매수했는데 하락추세다!
                if PickCoinInfo['BuyTrendOK'] == True and IsDownTrend == True:

                    #시장가 주문을 넣는다!
                    balances = myBithumb.SellCoinMarket(ticker,PickCoinInfo['BuyTrendVolume'])

                    PickCoinInfo['BuyTrendOK'] = False
                    msg = ticker + " 별은 봇 하락 추세가 확인되어 이전에 매수한 " + str(TrendMoneyRate*10) + "% 비중 " + str(PickCoinInfo['BuyTrendVolume']*CurrentPrice)+ "원어치 매도 했어요!"
                    PickCoinInfo['BuyTrendVolume'] = 0
                    print(msg)  
                    line_alert.SendMessage(msg) 

            #########################################################
            #########################################################
            #########################################################

            



            BB60_2_before2 = myBithumb.GetBB(df,60,-3)
            BB60_2_before = myBithumb.GetBB(df,60,-2)

            BB60_1_before2 = myBithumb.GetBB(df,60,-3)
            BB60_1_before = myBithumb.GetBB(df,60,-2)

            print("---------------------------")
            pprint.pprint(BB60_2_before2)
            pprint.pprint(BB60_1_before2)
            print("---------------------------")
            pprint.pprint(BB60_2_before)
            pprint.pprint(BB60_1_before)
            print("---------------------------")


            Candle_before2 = df['close'].iloc[-3]
            Candle_before = df['close'].iloc[-2]


            #양봉 캔들인지 여부
            IsUpCandle = False

            #시가보다 종가가 크다면 양봉이다
            if df['open'].iloc[-2] <= df['close'].iloc[-2]:
                IsUpCandle = True

            print("IsUpCandle : ", IsUpCandle)




            #########################################################
            #5개 라인을 이전봉 양봉으로 상단 돌파 했는지
            #이전봉 음봉으로 하단 돌파했는지 여부로
            #단타 매매 결정!

            IsBuy = False
            IsSell = False
            

            '--------------------------------------------------------------------------------------'
            #맨위

            if IsUpTrend == True:
                #상향돌파 여부 이전엔 업라인 아래에 있다가 어제 업라인을 돌파했고 양봉이었다!
                if Candle_before2 < BB60_2_before2['upper'] and BB60_2_before['upper'] < Candle_before and IsUpCandle == True:
                    IsBuy = True

            #하향돌파 여부 이전엔 업라인 위에에 있다가 어제 업라인을 아래로 돌파했고 음봉이었다!
            if Candle_before2 > BB60_2_before2['upper'] and BB60_2_before['upper'] > Candle_before and IsUpCandle == False:
                IsSell = True
            '--------------------------------------------------------------------------------------'
            #위 중간


            if IsUpTrend == True:
                #상향돌파 여부 이전엔 업라인 아래에 있다가 어제 업라인을 돌파했고 양봉이었다!
                if Candle_before2 < BB60_1_before2['upper'] and BB60_1_before['upper'] < Candle_before and IsUpCandle == True:
                    IsBuy = True

            #하향돌파 여부 이전엔 업라인 위에에 있다가 어제 업라인을 아래로 돌파했고 음봉이었다!
            if Candle_before2 > BB60_1_before2['upper'] and BB60_1_before['upper'] > Candle_before and IsUpCandle == False:
                IsSell = True

            '--------------------------------------------------------------------------------------'
            #중앙선
            #상향돌파 여부 이전엔 업라인 아래에 있다가 어제 업라인을 돌파했고 양봉이었다!
            if Candle_before2 < BB60_1_before2['ma'] and BB60_1_before['ma'] < Candle_before and IsUpCandle == True:
                IsBuy = True

            #하향돌파 여부 이전엔 업라인 위에에 있다가 어제 업라인을 아래로 돌파했고 음봉이었다!
            if Candle_before2 > BB60_1_before2['ma'] and BB60_1_before['ma'] > Candle_before and IsUpCandle == False:
                IsSell = True
            '--------------------------------------------------------------------------------------'
            #아래 중간
            #상향돌파 여부 이전엔 다운라인 아래에 있다가 어제 다운라인을 돌파했고 양봉이었다!
            if Candle_before2 < BB60_1_before2['lower'] and BB60_1_before['lower'] < Candle_before and IsUpCandle == True:
                IsBuy = True

            if IsDownTrend == True:
                #하향돌파 여부 이전엔 다운라인 위에에 있다가 어제 다운라인을 아래로 돌파했고 음봉이었다!
                if Candle_before2 > BB60_1_before2['lower'] and BB60_1_before['lower'] > Candle_before and IsUpCandle == False:
                    IsSell = True
            '--------------------------------------------------------------------------------------'
            #맨아래
            #상향돌파 여부 이전엔 다운라인 아래에 있다가 어제 다운라인을 돌파했고 양봉이었다!
            if Candle_before2 < BB60_2_before2['lower'] and BB60_2_before['lower'] < Candle_before and IsUpCandle == True:
                IsBuy = True

            if IsDownTrend == True:
                #하향돌파 여부 이전엔 다운라인 위에에 있다가 어제 다운라인을 아래로 돌파했고 음봉이었다!
                if Candle_before2 > BB60_2_before2['lower'] and BB60_2_before['lower'] > Candle_before and IsUpCandle == False:
                    IsSell = True
            '--------------------------------------------------------------------------------------'



            #########################################################
            #캔들 패턴으로 매매 신호 발생!!

            if Candle_before <= BB60_1_before['lower']:

                df['morningstar'] = GMA_Candle.detect_morningstar(df)
                df['morningdojistar'] = GMA_Candle.detect_morningdojistar(df)
                df['engulfing'] = GMA_Candle.detect_engulfing(df)
                df['piercing'] = GMA_Candle.detect_piercing(df)
                df['hammer'] = GMA_Candle.detect_hammer(df)

                if df['morningstar'].iloc[-2] == 100 or df['morningdojistar'].iloc[-2] == 100 or df['engulfing'].iloc[-2] == 100 or df['piercing'].iloc[-2] == 100 or df['hammer'].iloc[-2] == 100:
                    IsBuy = True

            if Candle_before >= BB60_1_before['upper']:

                df['eveningstar'] = GMA_Candle.detect_eveningstar(df)
                df['eveningdojistar'] = GMA_Candle.detect_eveningdojistar(df)
                df['darkcloudcover'] = GMA_Candle.detect_darkcloudcover(df)
                df['bearishengulfing'] = GMA_Candle.detect_bearishengulfing(df)
                df['shootingstar'] = GMA_Candle.detect_shootingstar(df)

                if df['eveningstar'].iloc[-2] == 100 or df['eveningdojistar'].iloc[-2] == 100 or df['darkcloudcover'].iloc[-2] == 100 or df['bearishengulfing'].iloc[-2] == 100 or df['shootingstar'].iloc[-2] == 100:
                    IsSell = True





            IsFull = True #풀매수 상태 구분!
            for DantaData in list(PickCoinInfo['DantaList']):
                #아직 매수되지 않은 슬롯을 찾는다!
                if DantaData['IsBuy'] == False:
                    IsFull = False
                    break

            #상향 돌파 했는데 풀 매수 상태이거나  하향돌파했는데 매도 해야 되는 상황이다!
            if (IsBuy == True and IsFull == True) or IsSell == True:

                IsDone = False
                
                # 지정한 수익률(1.5%)보다 높은 건 다 매도처리 한다!
                for DantaData in list(PickCoinInfo['DantaList']):
                    if DantaData['IsBuy'] == True:

                        #진입가격에서 1.5%위에 있는 가격을 구한다
                        RevenuePrice = DantaData['EntryPrice'] * (1.0 + DANTA_TARGET_REVENUE)

                        #그 가격보다 현재가가 위에 있다면 매도한다!
                        if RevenuePrice <= CurrentPrice: 

                            #저장된 단타수량을 매도!
                            myBithumb.SellCoinMarket(ticker,DantaData['DantaAmt'])

                            SellMoney = DantaData['DantaAmt'] * CurrentPrice

                            msg = ticker + " 별은 봇 ID:" + str(DantaData['Id']) + " -> ["+str(SellMoney)+"]원어치 단타방법에서 익절로 팔았어요!!!!"
                            print(msg) 
                            line_alert.SendMessage(msg) 

                            #전량 매도 모두 초기화! 
                            DantaData['IsBuy'] = False
                            DantaData['EntryPrice'] = 0
                            DantaData['DantaAmt'] = 0

                            #파일에 저장
                            with open(strategy_info_file_path, 'w') as outfile:
                                json.dump(StrategyInfoList, outfile)

                            IsDone = True #1개라도 팔았다면 True로 변경!

                            #상향돌파 한거는 1개만 팔아준다!
                            if IsBuy == True:
                                break



                #팔아야 되는데 못 팔았다? 그런데 풀매수 상태다?
                if IsSell == True and IsDone == False  and IsFull == True:
                    #1개 손절해서 슬롯을 비워준다!

                    #가장 진입가격이 높은거를 비워준다 진입 가격순으로 정렬해서!
                    PickData = sorted(list(PickCoinInfo['DantaList']), key=lambda coin_info: (coin_info['EntryPrice']), reverse= True)
                    #이곳에는 진입가격 가장높은거의 ID!
                    PickId = PickData[0]['Id']

                    for DantaData in list(PickCoinInfo['DantaList']):
                        if DantaData['Id'] == PickId:

                            #저장된 단타수량을 매도!
                            myBithumb.SellCoinMarket(ticker,DantaData['DantaAmt'])

                            SellMoney = DantaData['DantaAmt'] * CurrentPrice

                            msg = ticker + " 별은 봇 ID:" + str(DantaData['Id']) + " -> ["+str(SellMoney)+"]원어치 단타방법으로 손절로 팔았어요!!!!"
                            print(msg) 
                            line_alert.SendMessage(msg) 

                            #전량 매도 모두 초기화! 
                            DantaData['IsBuy'] = False
                            DantaData['EntryPrice'] = 0
                            DantaData['DantaAmt'] = 0

                            #파일에 저장
                            with open(strategy_info_file_path, 'w') as outfile:
                                json.dump(StrategyInfoList, outfile)

                            break
            
            #
            else:

                #매수해야 된다면!
                if IsBuy == True:
                    
                    
                    for DantaData in list(PickCoinInfo['DantaList']):
                        #아직 매수되지 않은 슬롯을 찾는다!
                        if DantaData['IsBuy'] == False:

                            #발견했다면 매수!
                            BuyAmt = float(StMoney / CurrentPrice)


                            DantaData['IsBuy'] = True
                            DantaData['EntryPrice'] = CurrentPrice #현재가로 진입했다고 가정합니다!
                            DantaData['DantaAmt'] = BuyAmt

                
                            #시장가 주문을 넣는다!
                            balances = myBithumb.BuyCoinMarket(ticker,StMoney)

                            msg = ticker + " 별은 봇 " + str(StMoney) + "원어치 "  +  str(CurrentPrice) + "가격으로 단타 매수 완료!"
                            print(msg) 
                            line_alert.SendMessage(msg) 

                            break



            PickCoinInfo['DateStrForToday'] = day_str #날짜를 저장해 둔다!

            #파일에 저장
            with open(strategy_info_file_path, 'w') as outfile:
                json.dump(StrategyInfoList, outfile)


import schedule      
if __name__ == "__main__":
    trading_in_progress = False
    Bithumb_BB_Bot()  # 테스트용 즉시 실행
    #get_coin_list()
    schedule.every().hour.at(":01").do(Bithumb_BB_Bot)
    while True:
        schedule.run_pending()
        time.sleep(1)