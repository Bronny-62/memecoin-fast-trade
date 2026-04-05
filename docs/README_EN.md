# MemeCoin Fast Trade

English | [中文](../README.md) | [日本語](README_JA.md) | [한국어](README_KO.md)

A sub-second MemeCoin buying system powered by real-time Twitter monitoring and keyword matching.

> **Disclaimer**: This project is a trading assistance tool only. It does not constitute investment advice, nor does it guarantee any trading outcome. Automated trading carries the risk of financial loss -- all trading decisions and their consequences are solely the user's responsibility. Please ensure compliance with applicable laws and platform terms of service before use.

## Overview

The core objective of MemeCoin Fast Trade is to **execute a token purchase the moment a target KOL tweets**.

Supported chains: Solana / BSC / Base / XLayer / Ethereum / Avax / MegaETH

**Example Scenario**

You have configured the monitored user `@elonmusk`, the keyword `DOGE`, and mapped it to a token address on the Solana chain. When Elon Musk publishes a tweet containing "DOGE", the system identifies it within 1 second, sends the token address to a Telegram trading bot, and automatically triggers a fast buy of DOGE on Solana.

**Workflow**

```
Tweet -> Real-time signal source -> Keyword matching -> Token address extraction -> Telegram Bot auto-order
```

**Core Capabilities**

- Dual signal source: `gmgn_monitor_extension` Chrome extension (free) or external WebSocket service
- High-performance keyword matching via Aho-Corasick automaton
- `T0/T1` tiered user and keyword strategy
- BSC hits -> `@SigmaTrading7_bot` / XLayer hits -> `@based_eth_bot`
- Automatic Telegram authorization and Bot connectivity verification on startup
- API endpoints: `/health`, `/reload_config`, `/xlayer_status`, `/ws`

## Quick Start

### 1. Requirements

- Python 3.8+
- Virtual environment `.venv` recommended

### 2. Configuration

Edit the following files before launch:

| File | Purpose |
|------|---------|
| `config/config.ini` | Telegram API credentials, trading bots, signal source URL, listen port |
| `config/token_mapping.json` | Keyword-to-token-address mapping |
| `config/monitored_users.json` | Monitored user lists by tier |

### 3. Launch

```bash
# macOS / Linux
./start_monitor.sh

# Windows
start_monitor.bat
```

The launch script automatically installs dependencies, verifies Telegram sessions, checks bot connectivity, and starts the listening service.

Debug mode:

```bash
PYTHONPATH=src python -m monitoring_service
```

## Signal Source (choose one)

### Option A: `gmgn_monitor_extension` Browser Extension

Intercepts WebSocket data from the gmgn.ai Twitter monitoring page and forwards it to this system via a Chrome extension.

**Install**

1. Open `chrome://extensions/` in Chrome, enable **Developer mode**
2. Click **Load unpacked**, select the `gmgn_monitor_extension` folder in this project

**Connect**

1. Start this system
2. Click the extension icon in the toolbar to open the side panel
3. Navigate to [gmgn.ai/follow?chain=bsc](https://gmgn.ai/follow?chain=bsc)
4. Click `Trade System Connect` in the side panel -- a green indicator means success

The extension runs in the background -- closing the side panel does not interrupt interception or forwarding.

### Option B: External WebSocket Signal Source

Connect via a third-party paid Twitter real-time monitoring service. No browser extension required.

Recommended: [1fastx.com](https://www.notion.so/shingle/1fastx-com-23c4e44711ff802f8df9cfd83fe4d5c0) -- sub-second Twitter monitoring WebSocket push service.

After purchasing the service on 1fastx.com, you will receive a dedicated WebSocket URL. Enter it in `config/config.ini`:

```ini
[Source]
ws_url = wss://your-purchased-websocket-url
```

The system connects automatically on startup.

## Telegram Bot Setup

This system supports two TG trading bots (`@SigmaTrading7_bot` and `@based_eth_bot`) and you can choose the setup that fits your workflow:

- Use either one: if a single bot already covers your target chains, you can run with only that bot;
- Mix by chain: you can also split chains across bots, for example using SigmaBot for some chains and BasedBot for others.

BasedBot also supports multiple chains and is not limited to XLayer. For supported chains, fees, and features, always follow the latest official bot information.

### `@SigmaTrading7_bot` (BSC)

1. Search `@SigmaTrading7_bot` in Telegram -> `/start`
2. Complete account and wallet setup
3. Navigate to `Settings` -> `Auto Buy` -> select target chain -> enable Auto Buy

Supported chains (current): MegaETH / Base / Ethereum / Avax / BSC / Solana

Recommended usage: prioritize `BSC` and `Solana` (SOL) trading scenarios.

> Auto Buy must be enabled, otherwise pushed token addresses will not trigger purchases.

### `@based_eth_bot` (XLayer)

1. Search `@based_eth_bot` in Telegram -> `/start`
2. Complete account and trading parameter setup
3. Ensure the bot has an active conversation with your account

Supported chains (current): Base / Ethereum / Binance(BSC) / Abstract / Avalanche / HyperEVM / Arbitrum / Ink / Story / XLayer / Plasma / UniChain / Monad / MegaETH / Tempo / Solana

Recommended usage: prioritize `XLayer`, `Base` (Based), and other EVM-oriented trading scenarios. It can also be combined with SigmaBot by chain.

> The system cannot send messages to an uninitialized bot.

## Configuration Reference

### `config/config.ini`

| Section | Key | Description |
|---------|-----|-------------|
| `[Telegram]` | `api_id` / `api_hash` | Telegram developer credentials |
| | `sigma_bot_username` / `sigma_bot_id` | BSC trading bot |
| | `BasedBot_username` / `BasedBot_id` | XLayer trading bot |
| | `proxy_type` / `proxy_addr` / `proxy_port` | Proxy config (optional) |
| `[Source]` | `ws_url` | External WebSocket URL (leave empty to disable) |
| `[Server]` | `listen_port` | Local listen port, default `8051` |

### `config/token_mapping.json`

`SigmaBot_T0_KEYS` / `SigmaBot_T1_KEYS` / `SigmaBot_CHANGE_IMAGE` / `BasedBot_T0_KEYS` / `BasedBot_T1_KEYS` / `BasedBot_CHANGE_IMAGE`

### `config/monitored_users.json`

`SigmaBot_T0_Users` / `SigmaBot_T1_Users` / `BasedBot_T0_Users` / `BasedBot_T1_Users`

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | System health and runtime stats |
| `GET /reload_config` | Hot-reload keywords and monitored users |
| `GET /xlayer_status` | XLayer status |
| `WS /ws` | Extension message ingestion |

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Service won't start | Check Python version, dependencies, port conflicts |
| Telegram unauthorized | Re-run the launch script and follow the auth prompts |
| Bot unresolvable | Manually open the bot in Telegram and send `/start` |
| No data from extension | Confirm gmgn.ai monitoring page is open and `Trade System Connect` is clicked |
| WebSocket not connecting | Verify `ws_url` in `config/config.ini` |
| Keywords not triggering | Check user tiers, keyword config, and terminal logs |

## License

[MIT](../LICENSE)
