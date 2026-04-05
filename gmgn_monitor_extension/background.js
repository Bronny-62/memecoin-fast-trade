// background.js - Service Worker for gmgn_monitor_extension
// Keeps interceptor and forwarding active even when side panel is closed.

const TRADE_V1_URL = 'ws://localhost:8051/ws';
const ALLOWED_CHANNELS = ['twitter_user_monitor_basic'];
const MAX_LOG_ENTRIES = 1000;
const LOG_CLEANUP_BATCH = 950;

let tradeWS = null;
let isTradeConnected = false;
let isInjectorInstalled = false;
let isInterceptorActive = false;
let pageStatus = 'Waiting for page...';
let capturedCount = 0;
let filteredCount = 0;
let totalWsCount = 0;
let logs = [];

function pushLog(prefix, message) {
  logs.push({
    time: new Date().toLocaleTimeString(),
    prefix,
    message: typeof message === 'object' ? JSON.stringify(message) : String(message)
  });
  if (logs.length > MAX_LOG_ENTRIES) {
    logs.splice(0, LOG_CLEANUP_BATCH);
    logs.push({
      time: new Date().toLocaleTimeString(),
      prefix: 'System',
      message: 'Old logs auto-cleaned to save memory...'
    });
  }
}

function getPublicState() {
  return {
    isTradeConnected,
    isInjectorInstalled,
    isInterceptorActive,
    pageStatus,
    capturedCount,
    filteredCount,
    logs
  };
}

function broadcastState() {
  chrome.runtime.sendMessage({
    type: 'BG_STATE_UPDATE',
    state: getPublicState()
  }).catch(() => {});
}

function updateInterceptorStatusFromTraffic() {
  if (isInjectorInstalled && (filteredCount > 0 || capturedCount > 0 || totalWsCount > 0)) {
    isInterceptorActive = true;
  }
}

function connectToTrade() {
  if (tradeWS) {
    try {
      tradeWS.close();
    } catch (e) {}
    tradeWS = null;
  }

  tradeWS = new WebSocket(TRADE_V1_URL);

  tradeWS.onopen = () => {
    isTradeConnected = true;
    pushLog('Trade', 'Connected to Trade System (8051)');
    broadcastState();
  };

  tradeWS.onclose = () => {
    isTradeConnected = false;
    tradeWS = null;
    pushLog('Trade', 'Disconnected from Trade System');
    broadcastState();
  };

  tradeWS.onerror = () => {
    pushLog('Error', 'Trade System connection error. Is it running?');
    broadcastState();
  };
}

function clearPanelCounters() {
  capturedCount = 0;
  filteredCount = 0;
  pageStatus = 'Waiting for page...';
  // Keep interceptor status because page injection can still be valid.
  logs = [];
}

function handleGmgnMessage(rawData) {
  totalWsCount++;
  pageStatus = 'Active';

  let parsedData;
  try {
    parsedData = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;
  } catch (e) {
    capturedCount++;
    updateInterceptorStatusFromTraffic();
    pushLog('GMGN_RAW', rawData);
    broadcastState();
    return;
  }

  const channel = parsedData.channel || '';
  if (!ALLOWED_CHANNELS.includes(channel)) {
    filteredCount++;
    pageStatus = 'Active';
    updateInterceptorStatusFromTraffic();
    broadcastState();
    return;
  }

  capturedCount++;
  updateInterceptorStatusFromTraffic();
  pushLog(`GMGN [${channel || 'unknown'}]`, parsedData);

  if (isTradeConnected && tradeWS && tradeWS.readyState === WebSocket.OPEN) {
    try {
      tradeWS.send(JSON.stringify(parsedData));
    } catch (e) {
      pushLog('Trade Error', `Send failed: ${e.message}`);
    }
  }
  broadcastState();
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || typeof message !== 'object') {
    return false;
  }

  if (message.type === 'GMGN_INJECTOR_STATUS') {
    isInjectorInstalled = true;
    updateInterceptorStatusFromTraffic();
    pushLog('System', 'Interceptor injected successfully on page.');
    broadcastState();
    return false;
  }

  if (message.type === 'GMGN_WS_MESSAGE') {
    handleGmgnMessage(message.payload);
    return false;
  }

  if (message.type === 'UI_GET_STATE') {
    sendResponse({ ok: true, state: getPublicState() });
    return true;
  }

  if (message.type === 'UI_TRADE_CONNECT') {
    connectToTrade();
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === 'UI_TRADE_DISCONNECT') {
    if (tradeWS) {
      tradeWS.close();
    }
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === 'UI_CLEAR_LOGS') {
    clearPanelCounters();
    broadcastState();
    sendResponse({ ok: true });
    return true;
  }

  return false;
});

// Open side panel when extension icon is clicked
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ windowId: tab.windowId });
});

// Auto-open side panel when user visits gmgn.ai
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('gmgn.ai')) {
    chrome.sidePanel.open({ windowId: tab.windowId }).catch((err) => {
      console.log('[gmgn_monitor_extension] Side panel auto-open skipped:', err.message);
    });
  }
});

console.log('[gmgn_monitor_extension] Background service worker initialized.');

