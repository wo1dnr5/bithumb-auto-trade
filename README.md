# 빗썸 자동매매 프로그램

이동평균선(MA5 / MA20) 골든크로스 / 데드크로스 전략을 사용하는 빗썸 자동매매 프로그램입니다.

## 전략

| 조건 | 동작 |
|------|------|
| MA5 > MA20 (골든크로스) + 미보유 | 보유 KRW의 30% 시장가 **매수** |
| MA5 < MA20 (데드크로스) + 보유 중 | 전량 시장가 **매도** |
| 그 외 | 대기 |

## 설치

```bash
pip3 install pybithumb
```

## 설정

`claude.py` 상단의 설정값을 수정합니다.

```python
ACCESS_KEY  = "YOUR_ACCESS_KEY"  # 빗썸 Access Key
SECRET_KEY  = "YOUR_SECRET_KEY"  # 빗썸 Secret Key

TICKER      = "BTC"              # 거래 종목 (BTC, ETH 등)
INVEST_RATE = 0.3                # 보유 KRW 중 매수에 사용할 비율
SHORT_MA    = 5                  # 단기 이동평균 기간
LONG_MA     = 20                 # 장기 이동평균 기간
INTERVAL    = "1h"               # 캔들 단위 (1m/3m/5m/10m/30m/1h/6h/12h/24h)
LOOP_SEC    = 60                 # 루프 주기 (초)
```

## API 키 발급

1. [빗썸](https://www.bithumb.com) 로그인
2. 마이페이지 → **API 관리**
3. **주문하기 + 잔고조회** 권한 체크 후 발급
4. 발급받은 키를 `claude.py`에 입력

> **주의:** API 키를 코드에 직접 입력한 후 GitHub에 올리지 마세요.

## 실행

```bash
python3 claude.py
```

## 실행 예시

```
2026-04-10 12:00:00 [INFO] API 연결 성공
2026-04-10 12:00:01 [INFO] BTC | 현재가: 130,000,000 | MA5: 129,500,000 | MA20: 128,000,000 | 보유: False
2026-04-10 12:00:01 [INFO] 조건 미충족 — 대기
```

로그는 화면과 `trade_log.txt` 파일에 동시에 기록됩니다.

## 주의사항

- 빗썸 API 등록 시 **허용 IP 주소**를 반드시 등록하세요.
- 실거래 전 소액으로 테스트하는 것을 권장합니다.
- 자동매매는 손실 위험이 있습니다.
