# MemeCoin Fast Trade

[English](README_EN.md) | [中文](../README.md) | [日本語](README_JA.md) | 한국어

실시간 트위터 모니터링과 키워드 매칭 기반의 MemeCoin 초단위 매수 시스템.

> **면책 조항**: 본 프로젝트는 거래 보조 도구로만 제공되며, 투자 조언을 제공하거나 거래 결과를 보장하지 않습니다. 자동 거래에는 자금 손실 위험이 따르며, 모든 거래 결정 및 그 결과는 사용자 본인의 책임입니다. 사용 전 대상 플랫폼과 해당 관할권의 관련 법규 및 서비스 약관을 준수하시기 바랍니다.

## 개요

MemeCoin Fast Trade의 핵심 목표는 **타겟 KOL이 트윗을 게시하는 순간 토큰 매수를 실행하는 것**입니다.

지원 체인: Solana / BSC / Base / XLayer / Ethereum / Avax / MegaETH

**사용 시나리오**

모니터링 사용자로 `@elonmusk`, 키워드로 `DOGE`, 그리고 Solana 체인의 토큰 주소를 매핑했다고 가정합니다. Elon Musk가 "DOGE"를 포함한 트윗을 게시하면, 시스템이 1초 이내에 이를 식별하고 토큰 주소를 Telegram 거래 Bot에 전송하여 Solana 체인에서 DOGE를 자동으로 빠르게 매수합니다.

**워크플로우**

```
트윗 -> 실시간 신호 소스 -> 키워드 매칭 -> 토큰 주소 추출 -> Telegram Bot 자동 주문
```

**핵심 기능**

- 이중 신호 소스: `gmgn_monitor_extension` Chrome 확장 프로그램(무료) 또는 외부 WebSocket 서비스
- Aho-Corasick 오토마톤 기반 고성능 키워드 매칭
- `T0/T1` 2단계 사용자 및 키워드 계층 전략
- BSC 히트 -> `@SigmaTrading7_bot` / XLayer 히트 -> `@based_eth_bot`
- 시작 시 Telegram 인증 및 Bot 연결 자동 검증
- API 엔드포인트: `/health`, `/reload_config`, `/xlayer_status`, `/ws`

## 빠른 시작

### 1. 환경 요구사항

- Python 3.8+
- 가상 환경 `.venv` 사용 권장

### 2. 설정

시작 전 다음 파일을 편집하세요:

| 파일 | 용도 |
|------|------|
| `config/config.ini` | Telegram API 자격 증명, 거래 Bot, 신호 소스 URL, 리스닝 포트 |
| `config/token_mapping.json` | 키워드-토큰 주소 매핑 |
| `config/monitored_users.json` | 계층별 모니터링 사용자 목록 |

### 3. 시작

```bash
# macOS / Linux
./start_monitor.sh

# Windows
start_monitor.bat
```

시작 스크립트가 의존성 설치, Telegram 세션 검증, Bot 연결 확인, 리스닝 서비스 시작을 자동으로 수행합니다.

디버그 모드:

```bash
PYTHONPATH=src python -m monitoring_service
```

## 신호 소스 연결 (둘 중 하나 선택)

### 방법 A: `gmgn_monitor_extension` 브라우저 확장 프로그램

Chrome 확장 프로그램을 통해 gmgn.ai 트위터 모니터링 페이지의 WebSocket 데이터를 가로채어 본 시스템으로 전달합니다.

**설치**

1. Chrome에서 `chrome://extensions/` 접속, **개발자 모드** 활성화
2. **압축해제된 확장 프로그램을 로드합니다** 클릭, 프로젝트 내 `gmgn_monitor_extension` 폴더 선택

**연결 방법**

1. 본 시스템 시작
2. 도구 모음의 확장 프로그램 아이콘을 클릭하여 사이드 패널 열기
3. [gmgn.ai/follow?chain=bsc](https://gmgn.ai/follow?chain=bsc) 접속
4. 사이드 패널에서 `Trade System Connect` 클릭 -- 녹색 표시등이 켜지면 성공

확장 프로그램은 백그라운드에서 상주합니다. 사이드 패널을 닫아도 가로채기와 전달은 계속됩니다.

### 방법 B: 외부 WebSocket 신호 소스

제3자 유료 트위터 실시간 모니터링 서비스를 통해 연결합니다. 브라우저 확장 프로그램이 필요 없습니다.

추천: [1fastx.com](https://www.notion.so/shingle/1fastx-com-23c4e44711ff802f8df9cfd83fe4d5c0) -- 초단위 트위터 모니터링 WebSocket 푸시 서비스.

1fastx.com에서 서비스를 구매하면 전용 WebSocket URL이 제공됩니다. 이를 `config/config.ini`의 `ws_url`에 입력하세요:

```ini
[Source]
ws_url = wss://your-purchased-websocket-url
```

시스템 시작 시 자동으로 연결됩니다.

## Telegram Bot 설정

본 시스템은 2가지 TG 거래 Bot(`@SigmaTrading7_bot`, `@based_eth_bot`)을 지원하며, 운용 방식에 따라 유연하게 선택할 수 있습니다.

- 하나만 선택: 단일 Bot이 목표 체인을 충분히 지원하면 해당 Bot만 사용해도 됩니다.
- 체인별 혼합 사용: 예를 들어 일부 체인은 SigmaBot, 다른 체인은 BasedBot으로 분리해서 사용할 수 있습니다.

BasedBot 역시 다중 체인을 지원하며 XLayer 전용이 아닙니다. 지원 체인, 수수료, 기능은 Bot 공식 최신 안내를 기준으로 확인하세요.

### `@SigmaTrading7_bot` (BSC)

1. Telegram에서 `@SigmaTrading7_bot` 검색 -> `/start`
2. 계정, 지갑 등 기본 설정 완료
3. `설정` -> `자동 구매` -> 대상 체인 선택 -> 자동 구매 활성화

지원 체인(현재): MegaETH / Base / Ethereum / Avax / BSC / Solana

추천 체인: `BSC` 및 `Solana`(SOL) 거래 시 우선적으로 사용하는 것을 권장합니다.

> 자동 구매가 활성화되지 않으면 푸시된 토큰 주소가 매수를 트리거하지 않습니다.

### `@based_eth_bot` (XLayer)

1. Telegram에서 `@based_eth_bot` 검색 -> `/start`
2. 계정 및 거래 매개변수 설정 완료
3. Bot과 현재 계정 간에 유효한 대화가 있는지 확인

지원 체인(현재): Base / Ethereum / Binance(BSC) / Abstract / Avalanche / HyperEVM / Arbitrum / Ink / Story / XLayer / Plasma / UniChain / Monad / MegaETH / Tempo / Solana

추천 체인: `XLayer`, `Base`(Based) 등 EVM 계열 거래에 우선적으로 사용하는 것을 권장하며, 필요 시 SigmaBot과 체인별로 나누어 함께 사용할 수도 있습니다.

> 초기화되지 않은 Bot에는 시스템에서 메시지를 보낼 수 없습니다.

## 설정 참조

### `config/config.ini`

| Section | Key | Description |
|---------|-----|-------------|
| `[Telegram]` | `api_id` / `api_hash` | Telegram 개발자 자격 증명 |
| | `sigma_bot_username` / `sigma_bot_id` | BSC 거래 Bot |
| | `BasedBot_username` / `BasedBot_id` | XLayer 거래 Bot |
| | `proxy_type` / `proxy_addr` / `proxy_port` | 프록시 설정 (선택사항) |
| `[Source]` | `ws_url` | 외부 WebSocket 주소 (비워두면 비활성화) |
| `[Server]` | `listen_port` | 로컬 리스닝 포트, 기본값 `8051` |

### `config/token_mapping.json`

`SigmaBot_T0_KEYS` / `SigmaBot_T1_KEYS` / `SigmaBot_CHANGE_IMAGE` / `BasedBot_T0_KEYS` / `BasedBot_T1_KEYS` / `BasedBot_CHANGE_IMAGE`

### `config/monitored_users.json`

`SigmaBot_T0_Users` / `SigmaBot_T1_Users` / `BasedBot_T0_Users` / `BasedBot_T1_Users`

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | 시스템 건강 상태 및 실행 통계 |
| `GET /reload_config` | 키워드 및 모니터링 사용자 핫 리로드 |
| `GET /xlayer_status` | XLayer 상태 조회 |
| `WS /ws` | 확장 프로그램 메시지 수신 엔트리 |

## 문제 해결

| 문제 | 해결 방법 |
|------|-----------|
| 서비스 시작 불가 | Python 버전, 의존성 설치, 포트 충돌 확인 |
| Telegram 미인증 | 시작 스크립트를 다시 실행하고 인증 프롬프트를 따름 |
| Bot 확인 불가 | Telegram에서 수동으로 Bot을 열고 `/start` 전송 |
| 확장 프로그램에서 데이터 없음 | gmgn.ai 모니터링 페이지가 열려 있고 `Trade System Connect`가 클릭되었는지 확인 |
| WebSocket 미연결 | `config/config.ini`의 `ws_url` 확인 |
| 키워드 미발동 | 사용자 계층, 키워드 설정, 터미널 로그 확인 |

## License

[MIT](../LICENSE)
