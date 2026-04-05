# MemeCoin Fast Trade

[English](README_EN.md) | [中文](../README.md) | 日本語 | [한국어](README_KO.md)

リアルタイムTwitter監視とキーワードマッチングによるMemeCoinの秒速購入システム。

> **免責事項**: 本プロジェクトは取引補助ツールとしてのみ提供されており、投資助言を行うものではなく、取引結果を保証するものでもありません。自動取引には資金損失のリスクが伴います。すべての取引判断とその結果は利用者自身の責任となります。使用前に、対象プラットフォームおよびお住まいの法域の関連法規・利用規約を遵守してください。

## 概要

MemeCoin Fast Trade の目的は、**ターゲットKOLがツイートした瞬間にトークンの購入を実行する**ことです。

対応チェーン: Solana / BSC / Base / XLayer / Ethereum / Avax / MegaETH

**利用シナリオ**

監視ユーザーに `@elonmusk`、キーワードに `DOGE`、対応するSolanaチェーン上のトークンアドレスを設定したとします。Elon Muskが "DOGE" を含むツイートを投稿すると、システムは1秒以内にそれを識別し、トークンアドレスをTelegram取引Botに送信して、Solana上のDOGEを自動購入します。

**ワークフロー**

```
ツイート -> リアルタイム信号ソース -> キーワードマッチ -> トークンアドレス抽出 -> Telegram Bot 自動注文
```

**コア機能**

- デュアル信号ソース: `gmgn_monitor_extension` Chrome拡張機能（無料）または外部WebSocketサービス
- Aho-Corasickオートマトンによる高速キーワードマッチング
- `T0/T1` 2層ユーザー・キーワード階層戦略
- BSCヒット -> `@SigmaTrading7_bot` / XLayerヒット -> `@based_eth_bot`
- 起動時にTelegram認証とBot接続を自動検証
- APIエンドポイント: `/health`、`/reload_config`、`/xlayer_status`、`/ws`

## クイックスタート

### 1. 動作環境

- Python 3.8+
- 仮想環境 `.venv` の使用を推奨

### 2. 設定

起動前に以下のファイルを編集してください:

| ファイル | 用途 |
|----------|------|
| `config/config.ini` | Telegram API認証情報、取引Bot、信号ソースURL、リスニングポート |
| `config/token_mapping.json` | キーワードとトークンアドレスのマッピング |
| `config/monitored_users.json` | 階層別監視ユーザーリスト |

### 3. 起動

```bash
# macOS / Linux
./start_monitor.sh

# Windows
start_monitor.bat
```

起動スクリプトは依存関係のインストール、Telegramセッション検証、Bot接続確認、リスニングサービスの開始を自動的に行います。

デバッグモード:

```bash
PYTHONPATH=src python -m monitoring_service
```

## 信号ソース接続（いずれか1つを選択）

### 方式A: `gmgn_monitor_extension` ブラウザ拡張機能

Chrome拡張機能でgmgn.aiのTwitter監視ページからWebSocketデータを傍受し、本システムに転送します。

**インストール**

1. Chromeで `chrome://extensions/` を開き、**デベロッパーモード**を有効化
2. **パッケージ化されていない拡張機能を読み込む**をクリックし、プロジェクト内の `gmgn_monitor_extension` フォルダを選択

**接続方法**

1. 本システムを起動
2. ツールバーの拡張機能アイコンをクリックしてサイドパネルを開く
3. [gmgn.ai/follow?chain=bsc](https://gmgn.ai/follow?chain=bsc) を開く
4. サイドパネルで `Trade System Connect` をクリック -- 緑色のインジケーターが点灯すれば成功

拡張機能はバックグラウンドで常駐します。サイドパネルを閉じても傍受と転送は継続されます。

### 方式B: 外部WebSocket信号ソース

サードパーティの有料Twitter リアルタイム監視サービスを通じて接続します。ブラウザ拡張機能は不要です。

推奨: [1fastx.com](https://www.notion.so/shingle/1fastx-com-23c4e44711ff802f8df9cfd83fe4d5c0) -- 秒単位のTwitter監視WebSocketプッシュサービス。

1fastx.comでサービスを購入すると、専用のWebSocket URLが提供されます。これを `config/config.ini` の `ws_url` に入力してください:

```ini
[Source]
ws_url = wss://your-purchased-websocket-url
```

システム起動時に自動的に接続されます。

## Telegram Bot 設定

本システムは 2 種類の TG 取引 Bot（`@SigmaTrading7_bot` と `@based_eth_bot`）に対応しており、運用方針に応じて柔軟に選択できます。

- どちらか一方を使用: 単一 Bot で対象チェーンをカバーできる場合は、その Bot のみで運用可能です。
- チェーンごとに併用: 例として、一部チェーンは SigmaBot、他のチェーンは BasedBot といった使い分けも可能です。

BasedBot も複数チェーンに対応しており、XLayer 専用ではありません。対応チェーン、手数料、機能は Bot 公式の最新情報を参照してください。

### `@SigmaTrading7_bot`（BSC）

1. Telegramで `@SigmaTrading7_bot` を検索 -> `/start`
2. アカウント・ウォレットの基本設定を完了
3. `設定` -> `自動購入` -> ターゲットチェーンを選択 -> 自動購入を有効化

対応チェーン（現時点）: MegaETH / Base / Ethereum / Avax / BSC / Solana

推奨チェーン: `BSC` と `Solana`（SOL）の取引シーンでの利用を推奨します。

> 自動購入が有効でない場合、プッシュされたトークンアドレスは購入をトリガーしません。

### `@based_eth_bot`（XLayer）

1. Telegramで `@based_eth_bot` を検索 -> `/start`
2. アカウントと取引パラメータの設定を完了
3. Botとアカウント間に有効な会話が存在することを確認

対応チェーン（現時点）: Base / Ethereum / Binance(BSC) / Abstract / Avalanche / HyperEVM / Arbitrum / Ink / Story / XLayer / Plasma / UniChain / Monad / MegaETH / Tempo / Solana

推奨チェーン: `XLayer`、`Base`（Based）などの EVM 系取引シーンでの利用を推奨します。また、チェーンごとに SigmaBot と併用することも可能です。

> 初期化されていないBotにはシステムからメッセージを送信できません。

## 設定リファレンス

### `config/config.ini`

| Section | Key | Description |
|---------|-----|-------------|
| `[Telegram]` | `api_id` / `api_hash` | Telegram開発者認証情報 |
| | `sigma_bot_username` / `sigma_bot_id` | BSC取引Bot |
| | `BasedBot_username` / `BasedBot_id` | XLayer取引Bot |
| | `proxy_type` / `proxy_addr` / `proxy_port` | プロキシ設定（任意） |
| `[Source]` | `ws_url` | 外部WebSocketアドレス（空欄で無効化） |
| `[Server]` | `listen_port` | ローカルリスニングポート、デフォルト `8051` |

### `config/token_mapping.json`

`SigmaBot_T0_KEYS` / `SigmaBot_T1_KEYS` / `SigmaBot_CHANGE_IMAGE` / `BasedBot_T0_KEYS` / `BasedBot_T1_KEYS` / `BasedBot_CHANGE_IMAGE`

### `config/monitored_users.json`

`SigmaBot_T0_Users` / `SigmaBot_T1_Users` / `BasedBot_T0_Users` / `BasedBot_T1_Users`

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | システムの健全性と実行統計 |
| `GET /reload_config` | キーワードと監視ユーザーのホットリロード |
| `GET /xlayer_status` | XLayerステータス照会 |
| `WS /ws` | 拡張機能メッセージ受信エントリ |

## トラブルシューティング

| 問題 | 対処方法 |
|------|----------|
| サービスが起動しない | Pythonバージョン、依存関係、ポート競合を確認 |
| Telegram未認証 | 起動スクリプトを再実行し、認証プロンプトに従う |
| Botが解決できない | Telegramで手動でBotを開き `/start` を送信 |
| 拡張機能からデータなし | gmgn.ai監視ページが開かれ `Trade System Connect` がクリックされていることを確認 |
| WebSocket未接続 | `config/config.ini` の `ws_url` を確認 |
| キーワードが発火しない | ユーザー階層、キーワード設定、ターミナルログを確認 |

## License

[MIT](../LICENSE)
