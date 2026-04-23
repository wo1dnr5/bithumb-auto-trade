# 빗썸 자동매매 프로그램

빗썸 거래소를 대상으로 한 자동매매 프로그램입니다. 기본 버전과 뉴스 감성 분석 버전 두 가지를 제공합니다.

---

## 파일 구성

| 파일 | 설명 |
|------|------|
| `bithumb_autotrading.py` | 기본 버전 — 이동평균선(MA) 전략 |
| `bithumb_autotrading_v2.py` | 고급 버전 — MA + 뉴스 감성 분석(Claude AI) 결합 |

---

## bithumb_autotrading.py — 기본 버전

### 전략

| 조건 | 동작 |
|------|------|
| MA5 > MA20 (골든크로스) + 미보유 | 보유 KRW의 30% 시장가 **매수** |
| MA5 < MA20 (데드크로스) + 보유 중 | 전량 시장가 **매도** |
| 그 외 | 대기 |

### 설치

```bash
pip3 install pybithumb
```

### 설정

`bithumb_autotrading.py` 상단의 설정값을 수정합니다.

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

### API 키 발급

1. [빗썸](https://www.bithumb.com) 로그인
2. 마이페이지 → **API 관리**
3. **주문하기 + 잔고조회** 권한 체크 후 발급
4. 발급받은 키를 `bithumb_autotrading.py`에 입력

### 실행

```bash
python3 bithumb_autotrading.py
```

### 실행 예시

```
2026-04-10 12:00:00 [INFO] API 연결 성공
2026-04-10 12:00:01 [INFO] BTC | 현재가: 130,000,000 | MA5: 129,500,000 | MA20: 128,000,000 | 보유: False
2026-04-10 12:00:01 [INFO] 조건 미충족 — 대기
```

---

## bithumb_autotrading_v2.py — 고급 버전 (MA + 뉴스 감성 분석)

### 전략

MA 신호와 뉴스 감성이 **같은 방향일 때만** 매매를 실행합니다.

```
MA 골든/데드크로스 신호
        +
CryptoPanic 뉴스 → Claude AI로 감성 판단
        ↓
둘 다 BUY  → 매수
둘 다 SELL → 매도
불일치     → 대기
```

| 조건 | 동작 |
|------|------|
| MA 골든크로스 + 뉴스 긍정 | **매수** |
| MA 데드크로스 + 뉴스 부정 | **매도** |
| 신호 불일치 | 대기 |

### 설치

```bash
pip3 install pybithumb anthropic requests
```

### 필요한 API 키 (3곳)

| API | 발급처 | 비용 |
|-----|--------|------|
| 빗썸 | bithumb.com → 마이페이지 → API 관리 | 무료 |
| Anthropic (Claude) | console.anthropic.com → API Keys | 유료 (종량제) |
| CryptoPanic | cryptopanic.com/developers/api | 무료 플랜 있음 |

### 설정

프로젝트 폴더에 `.env` 파일을 생성하고 아래 내용을 입력합니다.

```
BITHUMB_ACCESS_KEY=발급받은키
BITHUMB_SECRET_KEY=발급받은시크릿
ANTHROPIC_API_KEY=발급받은키
CRYPTOPANIC_API_KEY=발급받은키
```

> `.env` 파일은 `.gitignore` 및 `.dockerignore`에 포함되어 있어 이미지에 포함되거나 GitHub에 올라가지 않습니다.

### 실행

#### 로컬 실행

```bash
python3 bithumb_autotrading_v2.py
```

#### Docker 실행 (권장)

```bash
# 단독 실행
docker build -t bithumb-trade .
docker run -d --name bithumb-trade --env-file .env -v $(pwd)/logs:/app/logs bithumb-trade

# docker compose로 실행 (프로젝트 루트에서)
docker compose up -d bithumb-trade
```

컨테이너 로그 확인:

```bash
docker logs -f bithumb-trade
```

### 실행 예시

```
2026-04-10 12:00:00 [INFO] 빗썸 API 연결 성공
2026-04-10 12:00:03 [INFO] BTC | 현재가: 130,000,000 | MA5: 129,500,000 | MA20: 128,000,000 | MA신호: BUY | 뉴스감성: NEUTRAL | 보유: False
2026-04-10 12:00:03 [INFO] 신호 불일치 또는 조건 미충족 — 대기 (MA: BUY, 뉴스: NEUTRAL)
```

로그는 화면과 `trade_log_v2.txt` 파일에 동시에 기록됩니다.

---

## 업데이트 내역

### 2026-04-23
- **Docker 실행 환경 추가**: Dockerfile, .dockerignore, .env.example 추가
- **docker compose 지원**: 루트 docker-compose.yml에 서비스 등록
- **API 키 환경변수 전환**: `bithumb_autotrading_v2.py` 하드코딩 → `.env` + `python-dotenv` 방식으로 변경

---

## 주의사항

- 빗썸 API 등록 시 **허용 IP 주소**를 반드시 등록하세요.
- **API 키를 코드에 직접 입력한 후 GitHub에 올리지 마세요.** 반드시 `.env` 파일을 사용하세요.
- 실거래 전 소액으로 테스트하는 것을 권장합니다.
- 자동매매는 손실 위험이 있습니다.
