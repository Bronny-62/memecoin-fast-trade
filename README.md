# MemeCoin Fast Trade

[English](docs/README_EN.md) | 中文 | [日本語](docs/README_JA.md) | [한국어](docs/README_KO.md)

基于实时推特监控和关键词匹配的 MemeCoin 秒级快速买入系统。

> **Disclaimer**: 本项目仅作为交易辅助工具，不提供任何投资建议，亦不保证交易结果。自动化交易存在资金损失风险，所有交易决策及其后果由使用者自行承担。使用前请确保遵守目标平台及所在司法辖区的相关法律与服务条款。

## 功能简介

MemeCoin Fast Trade 的核心目标是：**在目标 KOL 发布推文的瞬间完成代币买入**。

支持公链：Solana / BSC / Base / XLayer / Ethereum / Avax / MegaETH

**使用场景示例**

你预设了监控用户 `@elonmusk`，关键词 `DOGE`，并映射了 Solana 链上的代币地址。当 Elon Musk 发布包含 "DOGE" 的最新推文时，系统在 1 秒内完成识别并将代币地址发送至 Telegram 交易 Bot，自动触发 Solana 链上 DOGE 的快速购买。

**工作流程**

```
推特推文 -> 实时监控信号源 -> 关键词匹配 -> 代币地址提取 -> Telegram Bot 自动下单
```

**核心能力**

- 双信号源接入：`gmgn_monitor_extension` 浏览器插件（免费）或外部 WebSocket 服务
- 基于 Aho-Corasick 自动机的高性能关键词匹配
- `T0/T1` 双层用户与关键词分级策略
- BSC 命中 -> `@SigmaTrading7_bot` / XLayer 命中 -> `@based_eth_bot`
- 启动时自动完成 Telegram 授权与 Bot 联通验证
- 提供 `/health`、`/reload_config`、`/xlayer_status`、`/ws` 接口

## Quick Start

### 1. 环境要求

- Python 3.8+
- 建议使用虚拟环境 `.venv`

### 2. 配置

启动前编辑以下文件：

| 文件 | 用途 |
|------|------|
| `config/config.ini` | Telegram API 凭证、交易 Bot、信号源地址、监听端口 |
| `config/token_mapping.json` | 关键词与代币地址映射 |
| `config/monitored_users.json` | 各层级监控用户名单 |

### 3. 启动

```bash
# macOS / Linux
./start_monitor.sh

# Windows
start_monitor.bat
```

启动脚本自动完成依赖安装、Telegram 会话校验、Bot 联通检查并启动监听服务。

调试模式：

```bash
PYTHONPATH=src python -m monitoring_service
```

## 信号源接入（二选一）

### 方式一：`gmgn_monitor_extension` 浏览器插件

通过 Chrome 扩展从 gmgn.ai 推特监控页拦截 WebSocket 数据并转发至本系统。

**安装插件**

1. Chrome 访问 `chrome://extensions/`，开启 **Developer mode**
2. 点击 **Load unpacked**，选择项目中的 `gmgn_monitor_extension` 文件夹

**连接使用**

1. 启动本系统
2. 点击工具栏插件图标打开侧边栏
3. 打开 [gmgn.ai/follow?chain=bsc](https://gmgn.ai/follow?chain=bsc)，确认进入推特监控页
4. 在侧边栏点击 `Trade System Connect`，连接指示灯变绿即启用成功

插件支持后台常驻 -- 关闭侧边栏后拦截与转发仍持续运行。

### 方式二：外部 WebSocket 信号源

通过第三方付费推特实时监控服务接入，无需浏览器插件。

推荐：[1fastx.com](https://www.notion.so/shingle/1fastx-com-23c4e44711ff802f8df9cfd83fe4d5c0) -- 提供秒级推特监控 WebSocket 推送服务。

在 1fastx.com 购买服务后，你会获得一个专属的 WebSocket 链接。将该链接填入 `config/config.ini` 的 `ws_url` 字段：

```ini
[Source]
ws_url = wss://your-purchased-websocket-url
```

启动系统后自动连接该信号源，无需额外操作。

## Telegram Bot 配置

本系统支持两类交易 TG Bot（`@SigmaTrading7_bot` 与 `@based_eth_bot`），可按你的交易习惯灵活选择：

- 二选一：若单个 Bot 已覆盖你的目标链，可统一使用其中一个；
- 搭配使用：也可按链路拆分，例如部分链走 SigmaBot，部分链走 BasedBot。

其中 BasedBot 同样支持多条链，并不只限于 XLayer；具体支持链、费率和功能请以 Bot 官方最新信息为准。

### `@SigmaTrading7_bot`（SOL/BSC）

1. Telegram 搜索 `@SigmaTrading7_bot` -> `/start`
2. 完成账户、钱包等基础设置
3. 进入 `设置` -> `自动购买` -> 选择目标链 -> 开启自动购买

支持链（当前）：MegaETH / Base / Ethereum / Avax / BSC / Solana

推荐链路：优先用于 `BSC` 与 `Solana`（SOL）交易场景。

> 未开启自动购买时，系统推送的代币地址不会触发买入。

### `@based_eth_bot`（Base/XLayer）

1. Telegram 搜索 `@based_eth_bot` -> `/start`
2. 完成账户与交易参数配置
3. 确保 Bot 已与当前账号建立过有效会话

支持链（当前）：Base / Ethereum / Binance(BSC) / Abstract / Avalanche / HyperEVM / Arbitrum / Ink / Story / XLayer / Plasma / UniChain / Monad / MegaETH / Tempo / Solana

推荐链路：优先用于 `XLayer`、`Base`（Based）等 EVM 系交易场景；也可按策略与 SigmaBot 分链搭配。

> Bot 未初始化时，系统无法向其发送消息。

## 配置参考

### `config/config.ini`

| Section | Key | Description |
|---------|-----|-------------|
| `[Telegram]` | `api_id` / `api_hash` | Telegram 开发者凭证 |
| | `sigma_bot_username` / `sigma_bot_id` | BSC 交易 Bot |
| | `BasedBot_username` / `BasedBot_id` | XLayer 交易 Bot |
| | `proxy_type` / `proxy_addr` / `proxy_port` | 代理配置（可选） |
| `[Source]` | `ws_url` | 外部 WebSocket 地址（留空则不启用） |
| `[Server]` | `listen_port` | 本地监听端口，默认 `8051` |

### `config/token_mapping.json`

`SigmaBot_T0_KEYS` / `SigmaBot_T1_KEYS` / `SigmaBot_CHANGE_IMAGE` / `BasedBot_T0_KEYS` / `BasedBot_T1_KEYS` / `BasedBot_CHANGE_IMAGE`

### `config/monitored_users.json`

`SigmaBot_T0_Users` / `SigmaBot_T1_Users` / `BasedBot_T0_Users` / `BasedBot_T1_Users`

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | 系统健康状态与运行统计 |
| `GET /reload_config` | 热重载关键词与监控用户配置 |
| `GET /xlayer_status` | XLayer 状态查询 |
| `WS /ws` | 插件消息接入入口 |

## Troubleshooting

| 问题 | 排查方向 |
|------|----------|
| 服务无法启动 | 检查 Python 版本、依赖安装、端口占用 |
| Telegram 未授权 | 重新执行启动脚本，按提示完成验证 |
| Bot 无法解析 | 先在 Telegram 中手动打开 Bot 并发送 `/start` |
| 插件无消息进入 | 确认已打开 gmgn.ai 监控页并点击 `Trade System Connect` |
| WebSocket 未连接 | 检查 `config/config.ini` 中 `ws_url` 是否有效 |
| 关键词未触发 | 检查用户分层、关键词配置与终端日志 |

## License

[MIT](LICENSE)
