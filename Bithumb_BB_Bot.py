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

    TotalMoney = myBithumb.GetTotalMoney(balances) #총 원금

    #내 평가금에서 투자하고 싶으면 아래 코드
    #TotalMoney = myBithumb.GetTotalRealMoney(balances) 

    #내 남은 원화(현금)
    RemainCash = myBithumb.GetCoinAmount(balances,"KRW")

    ######################################################
    #이런식으로 해당 전략에 할당할 금액을 조절
    InvestMoney = TotalMoney * 0.3 #30% 투자 적절히 수정!
    ######################################################


    #투자할 종목!
    InvestCoinList = ['KRW-ETH','KRW-ETC','KRW-DOGE','KRW-XRP','KRW-ELX','KRW-XTZ','KRW-PENGU','KRW-ENA'] #비트코인 


    CoinMoney = InvestMoney / len(InvestCoinList) #코인당 할당 금액

    #분할된 투자금!
    StMoney = CoinMoney / 10.0 #10분할!

    FixMoneyRate = 0.5 #10분할 중 2개를 항상 가져가는 비중으로 설정
    TrendMoneyRate = 4.75 #10분할 중 2개를 추세에 따라 정의
    DantaMoneyRate = 4.75 #10분할 중 6개를 단타로 활용 

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


            msg = ticker + " BB모아봇 첫 시작!!!!"
            print(msg) 
            line_alert.SendMessage(msg) 


            PickCoinInfo = InfinityDataDict
            #파일에 저장
            with open(strategy_info_file_path, 'w') as outfile:
                json.dump(StrategyInfoList, outfile)
                



        delay = '30m'
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

                    msg = ticker + " BB모아봇 " + str(FixMoneyRate*10) + "% 비중이 안차서 " + str(GapMoney)+ "원어치 매수 했어요!"
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

                msg = ticker + " BB모아봇 상승 추세가 확인되어 " + str(TrendMoneyRate*10) + "% 비중 " + str(LongTermTrendMoney)+ "원어치 매수 했어요!"
                print(msg)  
                line_alert.SendMessage(msg) 

            else:

                #이미 추세 비중 매수했는데 하락추세다!
                if PickCoinInfo['BuyTrendOK'] == True and IsDownTrend == True:

                    #시장가 주문을 넣는다!
                    balances = myBithumb.SellCoinMarket(ticker,PickCoinInfo['BuyTrendVolume'])

                    PickCoinInfo['BuyTrendOK'] = False
                    PickCoinInfo['BuyTrendVolume'] = 0
                    msg = ticker + " BB모아봇 하락 추세가 확인되어 이전에 매수한 " + str(TrendMoneyRate*10) + "% 비중 " + str(PickCoinInfo['BuyTrendVolume']*CurrentPrice)+ "원어치 매도 했어요!"
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

                            msg = ticker + " BB모아봇 ID:" + str(DantaData['Id']) + " -> ["+str(SellMoney)+"]원어치 단타세계관에서 익절로 팔았어요!!!!"
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

                            msg = ticker + " BB모아봇 ID:" + str(DantaData['Id']) + " -> ["+str(SellMoney)+"]원어치 단타세계관에서 손절로 팔았어요!!!!"
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

                            msg = ticker + " BB모아봇 " + str(StMoney) + "원어치 "  +  str(CurrentPrice) + "가격으로 단타 매수 완료!"
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
    schedule.every().hour.at(":01").do(Bithumb_BB_Bot)
    schedule.every().hour.at(":31").do(Bithumb_BB_Bot)
    while True:
        schedule.run_pending()
        time.sleep(1)