const tradeStatus = document.getElementById('trade-status');
const tradeDot = document.getElementById('trade-dot');
const connectTradeBtn = document.getElementById('connect-trade-btn');
const logsDiv = document.getElementById('logs');
const msgCountSpan = document.getElementById('msg-count');
const filteredCountSpan = document.getElementById('filtered-count');
const pageDot = document.getElementById('page-dot');
const pageStatus = document.getElementById('page-status');
const injectorDot = document.getElementById('injector-dot');
const injectorStatus = document.getElementById('injector-status');

let isTradeConnected = false;
let lastRenderedLogs = '';

function updateTradeStatus(connected) {
  isTradeConnected = connected;
  if (connected) {
    tradeDot.className = 'dot green';
    tradeStatus.textContent = 'Trade System (8051): Connected';
    connectTradeBtn.textContent = 'Disconnect Trade';
    connectTradeBtn.classList.add('secondary');
  } else {
    tradeDot.className = 'dot red';
    tradeStatus.textContent = 'Trade System (8051): Disconnected';
    connectTradeBtn.textContent = 'Trade System Connect';
    connectTradeBtn.classList.remove('secondary');
  }
}

function updatePageStatus(text) {
  pageStatus.textContent = text === 'Waiting for page...' ? text : 'Active';
  if (text && text !== 'Waiting for page...') {
    pageDot.className = 'dot green';
    return;
  }
  pageDot.className = 'dot';
}

function updateInjectorStatus(state) {
  if (state.isInterceptorActive) {
    injectorDot.className = 'dot green';
    injectorStatus.textContent = 'Injector: Active (Connected)';
    return;
  }
  if (state.isInjectorInstalled) {
    injectorDot.className = 'dot orange';
    injectorStatus.textContent = 'Injector: Installed (Waiting traffic)';
    return;
  }
  injectorDot.className = 'dot';
  injectorStatus.textContent = 'Injector: Pending';
}

function renderLogs(logs) {
  const serialized = JSON.stringify(logs || []);
  if (serialized === lastRenderedLogs) {
    return;
  }
  lastRenderedLogs = serialized;
  logsDiv.innerHTML = '';

  (logs || []).forEach((entry) => {
    const div = document.createElement('div');
    div.className = 'log-entry';

    const time = document.createElement('span');
    time.className = 'log-time';
    time.textContent = entry.time || '';

    const pre = document.createElement('span');
    pre.className = 'log-prefix';
    pre.textContent = `[${entry.prefix || 'System'}] `;

    const content = document.createElement('span');
    content.textContent = String(entry.message || '');

    if (content.textContent.length > 50) {
      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-btn';
      copyBtn.textContent = 'Copy';
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(content.textContent);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
          copyBtn.textContent = 'Copy';
        }, 1000);
      };
      div.appendChild(copyBtn);
    }

    div.appendChild(time);
    div.appendChild(pre);
    div.appendChild(content);
    logsDiv.appendChild(div);
  });

  logsDiv.scrollTop = logsDiv.scrollHeight;
}

function renderState(state) {
  if (!state) {
    return;
  }
  updateTradeStatus(Boolean(state.isTradeConnected));
  updatePageStatus(state.pageStatus);
  updateInjectorStatus(state);
  msgCountSpan.textContent = String(state.capturedCount || 0);
  filteredCountSpan.textContent = String(state.filteredCount || 0);
  renderLogs(state.logs || []);
}

connectTradeBtn.addEventListener('click', () => {
  chrome.runtime.sendMessage({
    type: isTradeConnected ? 'UI_TRADE_DISCONNECT' : 'UI_TRADE_CONNECT'
  }).catch(() => {});
});

document.getElementById('clear-logs').addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'UI_CLEAR_LOGS' }).catch(() => {});
});

chrome.runtime.onMessage.addListener((message) => {
  if (message && message.type === 'BG_STATE_UPDATE') {
    renderState(message.state);
  }
});

chrome.runtime.sendMessage({ type: 'UI_GET_STATE' }, (response) => {
  if (chrome.runtime.lastError) {
    return;
  }
  if (response && response.ok) {
    renderState(response.state);
  }
});
