// content.js
// Runs in the Isolated Extension world.
// 1. Injects injector.js into the page ASAP.
// 2. Listens for custom events from injector.js
// 3. Forwards data to extension runtime (handled by background worker).

// Aggressive Injection: Inject immediately
const injectScript = () => {
  try {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injector.js');
    script.onload = function() {
      this.remove();
    };
    (document.head || document.documentElement).appendChild(script);
    console.log('[GMGN Monitor] Injector script appended to document.');
  } catch (e) {
    console.error('[GMGN Monitor] Injection failed:', e);
  }
};

injectScript();

// Re-inject on page load just in case (for single page app navigations)
window.addEventListener('load', () => {
  // Check if we need to re-inject (injector.js handles duplicate checks)
  injectScript();
});

// Listen for injector ready signal
window.addEventListener('GMGN_INJECTOR_READY', () => {
  console.log('[GMGN Monitor] Injector signal received.');
  try {
    chrome.runtime.sendMessage({ type: 'GMGN_INJECTOR_STATUS', status: 'active' });
  } catch (e) {}
});

// Listen for the intercepted data
window.addEventListener('GMGN_WS_INTERCEPT', (event) => {
  const data = event.detail;
  if (!data) return;

  // Forward to extension runtime (background handles forwarding pipeline).
  try {
    chrome.runtime.sendMessage({
      type: 'GMGN_WS_MESSAGE',
      payload: data
    });
  } catch (e) {
    // Ignore transient runtime errors.
  }
});

console.log('[GMGN Monitor] Content script ready.');

