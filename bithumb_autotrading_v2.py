"""
빗썸 자동매매 프로그램 v2
전략: MA5/MA20 골든/데드크로스 + CryptoPanic 뉴스 감성 분석(Claude API) 결합
- MA 신호와 뉴스 감성이 같은 방향일 때만 매매 실행
"""

import pybithumb
import anthropic
import requests
import time
import logging

# ──────────────────────────────────────────
# 설정
# ──────────────────────────────────────────
BITHUMB_ACCESS_KEY  = "YOUR_BITHUMB_ACCESS_KEY"
BITHUMB_SECRET_KEY  = "YOUR_BITHUMB_SECRET_KEY"
ANTHROPIC_API_KEY   = "YOUR_ANTHROPIC_API_KEY"   # https://console.anthropic.com
CRYPTOPANIC_API_KEY = "YOUR_CRYPTOPANIC_API_KEY"  # https://cryptopanic.com/developers/api

TICKER      = "BTC"
INVEST_RATE = 0.3
SHORT_MA    = 5
LONG_MA     = 20
INTERVAL    = "1h"
LOOP_SEC    = 60
NEWS_COUNT  = 10   # 감성 분석에 사용할 최신 뉴스 개수

# ──────────────────────────────────────────
# 로깅
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("trade_log_v2.txt", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────
# 이동평균 / 잔고
# ──────────────────────────────────────────

def get_ma(ticker: str, period: int, interval: str) -> float:
    df = pybithumb.get_candlestick(ticker, interval=interval)
    if df is None or len(df) < period:
        return None
    return df["close"].rolling(period).mean().iloc[-1]


def get_krw_balance(bithumb) -> float:
    balance = bithumb.get_balance(TICKER)
    if balance is None:
        return 0.0
    return float(balance[2])


def get_coin_balance(bithumb) -> float:
    balance = bithumb.get_balance(TICKER)
    if balance is None:
        return 0.0
    return float(balance[0])


def get_current_price(ticker: str) -> float:
    return pybithumb.get_current_price(ticker)


def is_holding(bithumb) -> bool:
    return get_coin_balance(bithumb) > 0


# ──────────────────────────────────────────
# 뉴스 수집 (CryptoPanic)
# ──────────────────────────────────────────

def fetch_news(count: int = NEWS_COUNT) -> list[str]:
    """CryptoPanic에서 BTC 관련 최신 뉴스 헤드라인 수집"""
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": CRYPTOPANIC_API_KEY,
        "currencies": "BTC",
        "kind": "news",
        "filter": "hot",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        headlines = [item["title"] for item in results[:count]]
        return headlines
    except Exception as e:
        log.warning(f"뉴스 수집 실패: {e}")
        return []


# ──────────────────────────────────────────
# 감성 분석 (Claude API)
# ──────────────────────────────────────────

def analyze_sentiment(headlines: list[str]) -> str:
    """
    Claude API로 뉴스 헤드라인 감성 분석
    반환값: "BUY" | "SELL" | "NEUTRAL"
    """
    if not headlines:
        log.warning("분석할 뉴스 없음 → NEUTRAL 처리")
        return "NEUTRAL"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    headlines_text = "\n".join(f"- {h}" for h in headlines)

    prompt = f"""다음은 비트코인(BTC) 관련 최신 뉴스 헤드라인입니다.
경제 지표, 지정학적 이슈, 시장 분위기를 종합적으로 고려하여
비트코인 매매 관점에서 감성을 판단해주세요.

{headlines_text}

위 뉴스들을 바탕으로 현재 시장 분위기가
매수에 유리하면 BUY,
매도에 유리하면 SELL,
판단하기 어려우면 NEUTRAL
중 하나만 단답으로 대답하세요."""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        sentiment = message.content[0].text.strip().upper()
        if sentiment not in ("BUY", "SELL", "NEUTRAL"):
            sentiment = "NEUTRAL"
        return sentiment
    except Exception as e:
        log.warning(f"감성 분석 실패: {e}")
        return "NEUTRAL"


# ──────────────────────────────────────────
# 매매 로직
# ──────────────────────────────────────────

def trade(bithumb):
    # 1. MA 신호
    ma_short = get_ma(TICKER, SHORT_MA, INTERVAL)
    ma_long  = get_ma(TICKER, LONG_MA,  INTERVAL)

    if ma_short is None or ma_long is None:
        log.warning("이동평균 계산 실패 — 데이터 부족")
        return

    if ma_short > ma_long:
        ma_signal = "BUY"
    elif ma_short < ma_long:
        ma_signal = "SELL"
    else:
        ma_signal = "NEUTRAL"

    # 2. 뉴스 감성 신호
    headlines = fetch_news()
    sentiment = analyze_sentiment(headlines)

    # 3. 현재 상태
    price   = get_current_price(TICKER)
    holding = is_holding(bithumb)

    log.info(
        f"{TICKER} | 현재가: {price:,.0f} | "
        f"MA{SHORT_MA}: {ma_short:,.0f} | MA{LONG_MA}: {ma_long:,.0f} | "
        f"MA신호: {ma_signal} | 뉴스감성: {sentiment} | 보유: {holding}"
    )

    # 4. 두 신호가 모두 BUY → 매수
    if ma_signal == "BUY" and sentiment == "BUY" and not holding:
        krw        = get_krw_balance(bithumb)
        buy_amount = krw * INVEST_RATE
        if buy_amount < 5000:
            log.info("매수 가능 금액 부족 (최소 5,000원)")
            return
        result = bithumb.buy_market_order(TICKER, buy_amount)
        log.info(f"[매수] 금액: {buy_amount:,.0f}원 | 결과: {result}")

    # 5. 두 신호가 모두 SELL → 매도
    elif ma_signal == "SELL" and sentiment == "SELL" and holding:
        qty    = get_coin_balance(bithumb)
        result = bithumb.sell_market_order(TICKER, qty)
        log.info(f"[매도] 수량: {qty} | 결과: {result}")

    else:
        log.info(f"신호 불일치 또는 조건 미충족 — 대기 (MA: {ma_signal}, 뉴스: {sentiment})")


# ──────────────────────────────────────────
# 메인 루프
# ──────────────────────────────────────────

def main():
    log.info("=== 빗썸 자동매매 v2 시작 (MA + 뉴스 감성) ===")
    bithumb = pybithumb.Bithumb(BITHUMB_ACCESS_KEY, BITHUMB_SECRET_KEY)

    try:
        balance = bithumb.get_balance(TICKER)
        if balance is None:
            raise ValueError("빗썸 API 키가 올바르지 않습니다.")
        log.info("빗썸 API 연결 성공")
    except Exception as e:
        log.error(f"연결 실패: {e}")
        return

    while True:
        try:
            trade(bithumb)
        except Exception as e:
            log.error(f"오류 발생: {e}")
        time.sleep(LOOP_SEC)


if __name__ == "__main__":
    main()
