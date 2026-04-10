"""
빗썸 자동매매 프로그램
전략: 이동평균선(MA5 / MA20) 골든크로스 / 데드크로스
"""

import pybithumb
import time
import logging

# ──────────────────────────────────────────
# 설정
# ──────────────────────────────────────────
ACCESS_KEY = "YOUR_ACCESS_KEY"   # 빗썸 Access Key
SECRET_KEY = "YOUR_SECRET_KEY"   # 빗썸 Secret Key

TICKER      = "BTC"               # 거래 종목 (빗썸은 코인명만 입력: BTC, ETH 등)
INVEST_RATE = 0.3                 # 보유 KRW 중 매수에 사용할 비율 (0.3 = 30%)
SHORT_MA    = 5                   # 단기 이동평균 기간
LONG_MA     = 20                  # 장기 이동평균 기간
INTERVAL    = "1h"                # 캔들 단위 (1m/3m/5m/10m/30m/1h/6h/12h/24h)
LOOP_SEC    = 60                  # 루프 주기 (초)

# ──────────────────────────────────────────
# 로깅
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("trade_log.txt", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────

def get_ma(ticker: str, period: int, interval: str) -> float:
    """최근 캔들 데이터로 이동평균 계산"""
    df = pybithumb.get_candlestick(ticker, interval=interval)
    if df is None or len(df) < period:
        return None
    return df["close"].rolling(period).mean().iloc[-1]


def get_krw_balance(bithumb) -> float:
    """보유 KRW 잔고 조회"""
    balance = bithumb.get_balance(TICKER)
    if balance is None:
        return 0.0
    # get_balance 반환: (보유코인, 보유코인 가치, 보유KRW, 주문중KRW)
    return float(balance[2])


def get_coin_balance(bithumb) -> float:
    """보유 코인 잔고 조회"""
    balance = bithumb.get_balance(TICKER)
    if balance is None:
        return 0.0
    return float(balance[0])


def get_current_price(ticker: str) -> float:
    return pybithumb.get_current_price(ticker)


def is_holding(bithumb) -> bool:
    """해당 종목을 보유 중인지 확인"""
    return get_coin_balance(bithumb) > 0


# ──────────────────────────────────────────
# 매매 로직
# ──────────────────────────────────────────

def trade(bithumb):
    ma_short = get_ma(TICKER, SHORT_MA, INTERVAL)
    ma_long  = get_ma(TICKER, LONG_MA,  INTERVAL)

    if ma_short is None or ma_long is None:
        log.warning("이동평균 계산 실패 — 데이터 부족")
        return

    price   = get_current_price(TICKER)
    holding = is_holding(bithumb)

    log.info(
        f"{TICKER} | 현재가: {price:,.0f} | "
        f"MA{SHORT_MA}: {ma_short:,.0f} | MA{LONG_MA}: {ma_long:,.0f} | "
        f"보유: {holding}"
    )

    # 골든크로스 → 매수
    if ma_short > ma_long and not holding:
        krw        = get_krw_balance(bithumb)
        buy_amount = krw * INVEST_RATE
        if buy_amount < 5000:
            log.info("매수 가능 금액 부족 (최소 5,000원)")
            return
        result = bithumb.buy_market_order(TICKER, buy_amount)
        log.info(f"[매수] 금액: {buy_amount:,.0f}원 | 결과: {result}")

    # 데드크로스 → 매도
    elif ma_short < ma_long and holding:
        qty    = get_coin_balance(bithumb)
        result = bithumb.sell_market_order(TICKER, qty)
        log.info(f"[매도] 수량: {qty} | 결과: {result}")

    else:
        log.info("조건 미충족 — 대기")


# ──────────────────────────────────────────
# 메인 루프
# ──────────────────────────────────────────

def main():
    log.info("=== 빗썸 자동매매 시작 ===")
    bithumb = pybithumb.Bithumb(ACCESS_KEY, SECRET_KEY)

    # API 키 유효성 확인
    try:
        balance = bithumb.get_balance(TICKER)
        if balance is None:
            raise ValueError("API 키가 올바르지 않습니다.")
        log.info("API 연결 성공")
    except Exception as e:
        log.error(f"API 연결 실패: {e}")
        return

    while True:
        try:
            trade(bithumb)
        except Exception as e:
            log.error(f"오류 발생: {e}")
        time.sleep(LOOP_SEC)


if __name__ == "__main__":
    main()
