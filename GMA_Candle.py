#-*-coding:utf-8 -*-
'''

오류(버그)를 만난다면
검색이나 챗GPT등에 먼저 에러 로그를 
복사&붙여넣기로 알아 본 뒤 그래도 모르겠다면
댓글로 알려주세요 :)

게만아 파이썬 자동매매 수익 & 수강 후기
https://blog.naver.com/zacra/223568483228

'''

def detect_morningstar(df):
    # 3봉 패턴: 강한 하락(음봉) → 작은 몸통(양/음 상관없음) → 강한 상승(양봉)
    result = [0, 0]  # 첫 두 봉은 패턴 불가
    for i in range(2, len(df)):
        prev2 = df.iloc[i-2]
        prev1 = df.iloc[i-1]
        curr = df.iloc[i]
        # 1. 첫 봉 음봉, 2. 두번째 봉 몸통 작음, 3. 세번째 봉 양봉
        cond1 = prev2['close'] < prev2['open']
        cond2 = abs(prev1['close'] - prev1['open']) < abs(prev2['close'] - prev2['open']) * 0.5
        cond3 = curr['close'] > curr['open']
        cond4 = curr['close'] > ((prev2['open'] + prev2['close']) / 2)
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result

def detect_morningdojistar(df):
    # 3봉 패턴: 강한 하락(음봉) → 도지(십자형) → 강한 상승(양봉)
    result = [0, 0]
    for i in range(2, len(df)):
        prev2 = df.iloc[i-2]
        prev1 = df.iloc[i-1]
        curr = df.iloc[i]
        cond1 = prev2['close'] < prev2['open']
        cond2 = abs(prev1['close'] - prev1['open']) < (prev1['high'] - prev1['low']) * 0.1
        cond3 = curr['close'] > curr['open']
        cond4 = curr['close'] > ((prev2['open'] + prev2['close']) / 2)
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result

def detect_engulfing(df):
    # 2봉 패턴: 첫 봉 음봉, 두번째 봉 양봉이 전 봉을 완전히 감쌈
    result = [0]
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        cond1 = prev['close'] < prev['open']
        cond2 = curr['close'] > curr['open']
        cond3 = curr['open'] <= prev['close'] and curr['close'] > prev['open']
        result.append(100 if cond1 and cond2 and cond3 else 0)
    return result

def detect_piercing(df):
    # 2봉 패턴: 첫 봉 음봉, 두번째 봉 양봉이 전 봉 몸통의 중간 이상까지 침투
    result = [0]
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        cond1 = prev['close'] < prev['open']
        cond2 = curr['close'] > curr['open']
        cond3 = curr['open'] <= prev['close']
        cond4 = curr['close'] > (prev['open'] + prev['close']) / 2
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result

def detect_hammer(df):
    # 1봉 패턴: 아래꼬리가 길고, 몸통이 위에 위치 (양봉, 상승 반전 신호)
    result = []
    for i in range(len(df)):
        o = df.iloc[i]['open']
        c = df.iloc[i]['close']
        h = df.iloc[i]['high']
        l = df.iloc[i]['low']
        body = abs(c - o)
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        cond1 = lower_shadow > body * 2
        cond2 = upper_shadow < body
        cond3 = min(o, c) > (l + lower_shadow * 0.2)  # 몸통이 캔들 위쪽에 위치
        cond4 = c > o  # 양봉
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result


def detect_eveningstar(df):
    # 3봉 패턴: 강한 상승(양봉) → 작은 몸통(양/음 상관없음) → 강한 하락(음봉)
    result = [0, 0]  # 첫 두 봉은 패턴 불가
    for i in range(2, len(df)):
        prev2 = df.iloc[i-2]
        prev1 = df.iloc[i-1]
        curr = df.iloc[i]
        # 1. 첫 봉 양봉, 2. 두번째 봉 몸통 작음, 3. 세번째 봉 음봉
        cond1 = prev2['close'] > prev2['open']
        cond2 = abs(prev1['close'] - prev1['open']) < abs(prev2['close'] - prev2['open']) * 0.5
        cond3 = curr['close'] < curr['open']
        cond4 = curr['close'] < ((prev2['open'] + prev2['close']) / 2)
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result

def detect_eveningdojistar(df):
    # 3봉 패턴: 강한 상승(양봉) → 도지(십자형) → 강한 하락(음봉)
    result = [0, 0]
    for i in range(2, len(df)):
        prev2 = df.iloc[i-2]
        prev1 = df.iloc[i-1]
        curr = df.iloc[i]
        cond1 = prev2['close'] > prev2['open']
        cond2 = abs(prev1['close'] - prev1['open']) < (prev1['high'] - prev1['low']) * 0.1
        cond3 = curr['close'] < curr['open']
        cond4 = curr['close'] < ((prev2['open'] + prev2['close']) / 2)
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result

def detect_bearishengulfing(df):
    # 2봉 패턴: 첫 봉 양봉, 두번째 봉 음봉이 전 봉을 완전히 감쌈
    result = [0]
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        cond1 = prev['close'] > prev['open']
        cond2 = curr['close'] < curr['open']
        cond3 = curr['open'] >= prev['close'] and curr['close'] < prev['open']
        result.append(100 if cond1 and cond2 and cond3 else 0)
    return result

def detect_darkcloudcover(df):
    # 2봉 패턴: 첫 봉 양봉, 두번째 봉 음봉이 전 봉 몸통의 중간 이상까지 침투
    result = [0]
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        cond1 = prev['close'] > prev['open']
        cond2 = curr['close'] < curr['open']
        cond3 = curr['open'] >= prev['close']
        cond4 = curr['close'] < (prev['open'] + prev['close']) / 2
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result

def detect_shootingstar(df):
    # 1봉 패턴: 윗꼬리가 길고, 몸통이 아래에 위치 (음봉, 하락 반전 신호)
    result = []
    for i in range(len(df)):
        o = df.iloc[i]['open']
        c = df.iloc[i]['close']
        h = df.iloc[i]['high']
        l = df.iloc[i]['low']
        body = abs(c - o)
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        cond1 = upper_shadow > body * 2
        cond2 = lower_shadow < body
        cond3 = max(o, c) < (h - upper_shadow * 0.2)  # 몸통이 캔들 아래쪽에 위치
        cond4 = o > c  # 음봉
        result.append(100 if cond1 and cond2 and cond3 and cond4 else 0)
    return result
