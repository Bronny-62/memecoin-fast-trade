# GMGN Monitor Chrome Extension

## Overview

Intercepts WebSocket push data from `gmgn.ai`, filters messages from the `twitter_user_monitor_basic` channel, and forwards them in real-time to a local trade execution system for automated trading.

- Monkey-patches the page's WebSocket with zero interference to existing page behavior
- Side panel opens automatically when visiting `gmgn.ai`
- Side panel displays live connection status, message counters, and a scrolling log stream
- Service Worker runs persistently — data forwarding continues even when the side panel is closed

## Installation

### 1. Load the Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `gmgn_monitor_extension/` directory

### 2. Start the Local Trade System

Run the following command from the project root:

```bash
./start_monitor.sh
```

The WebSocket service must be running at `ws://localhost:8051/ws`.

### 3. Connect to the Trade System

1. Navigate to `https://gmgn.ai` — the side panel will open automatically
2. Click the **"Trade System Connect"** button in the side panel
3. A green dot and greyed-out button confirm a successful connection

### 4. Verify Status

The side panel shows three status indicators:

| Indicator | Description |
|-----------|-------------|
| Page Status | Green when the gmgn.ai page is loaded and active |
| Injector | Green when the WebSocket interceptor is active and receiving traffic |
| Trade System (8051) | Green when connected to the local trade system |

**Captured**: Number of `twitter_user_monitor_basic` channel messages forwarded to the trade system
**Filtered**: Number of messages from other channels that were discarded

## Collecting Data Samples

The log area displays intercepted raw data in real time:

1. Wait for tweet push entries to appear in the log area
2. Click the **"Copy"** button next to an entry (appears when the message length exceeds 50 characters)
3. Share the copied content with the developer for format mapping

## Troubleshooting

**Q: The side panel did not open automatically when I visited gmgn.ai.**
A: Click the extension icon in the Chrome toolbar to open it manually.

**Q: The Injector status stays at "Pending".**
A: Open Chrome DevTools (F12) and check the Console for errors. Also verify that a WebSocket connection was established under the Network tab.

**Q: Trade System shows "Disconnected".**
A: Verify the local service is running:

```bash
ps aux | grep terminal_server.py
```

**Q: Captured count is 0, but Filtered keeps increasing.**
A: This is expected behavior. The interceptor is working correctly, but no `twitter_user_monitor_basic` messages have been pushed yet. Wait for monitored users to post.

## Architecture

```
gmgn.ai WebSocket
    │
    ▼
injector.js          ← Runs in page MAIN world; monkey-patches the WebSocket constructor
    │  CustomEvent(GMGN_WS_INTERCEPT)
    ▼
content.js           ← Runs in extension ISOLATED world; bridges page events to the extension runtime
    │  chrome.runtime.sendMessage
    ▼
background.js        ← Service Worker; filters channels, manages state, forwards data
    │  WebSocket(ws://localhost:8051/ws)
    ▼
terminal_server.py   ← Local trade system; performs keyword matching and trade execution
    │
    ▼
side_panel.js        ← Side panel UI; polls background state and renders status/logs
```

## File Reference

| File | Description |
|------|-------------|
| `manifest.json` | Extension manifest (Manifest V3) |
| `background.js` | Service Worker: channel filtering, WebSocket forwarding, state management |
| `injector.js` | Injected into the page main world; patches WebSocket to capture all messages |
| `content.js` | Content script: injects `injector.js` and bridges page events to the extension runtime |
| `side_panel.html` | Side panel HTML layout |
| `side_panel.js` | Side panel logic: communicates with background, renders status and logs |
| `icons/` | Extension icons (16px, 48px, 128px) |

## Permissions

| Permission | Purpose |
|------------|---------|
| `sidePanel` | Access the Chrome Side Panel API |
| `scripting` | Dynamically inject content scripts |
| `tabs` | Listen for page load events to auto-open the side panel |
| `host_permissions: gmgn.ai/*` | Inject scripts into the target page |
| `host_permissions: localhost/*` | Connect to the local trade system WebSocket |
