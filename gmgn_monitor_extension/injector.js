// injector.js
// This script runs in the MAIN world (the page's context).
// It monkey-patches the WebSocket object to capture incoming messages.

(function() {
  console.log('[GMGN Monitor] Injector script starting...');
  
  const OriginalWebSocket = window.WebSocket;
  
  // Check if already patched
  if (window._GMGN_MONITOR_PATCHED) {
    console.log('[GMGN Monitor] Already patched, skipping.');
    return;
  }
  
  class InterceptedWebSocket extends OriginalWebSocket {
    constructor(...args) {
      console.log('[GMGN Monitor] New WebSocket created:', args[0]);
      super(...args);
      
      // Intercept onmessage setter
      let originalOnMessage = null;
      Object.defineProperty(this, 'onmessage', {
        get() {
          return originalOnMessage;
        },
        set(handler) {
          originalOnMessage = handler;
          // Wrap the handler
          const wrappedHandler = (event) => {
            try {
              const data = event.data;
              if (typeof data === 'string') {
                window.dispatchEvent(new CustomEvent('GMGN_WS_INTERCEPT', {
                  detail: data
                }));
              }
            } catch (e) {
              console.error('[GMGN Monitor] Intercept error:', e);
            }
            // Call original handler
            if (handler) {
              handler.call(this, event);
            }
          };
          // Set the wrapped handler on the underlying WebSocket
          OriginalWebSocket.prototype.__lookupSetter__('onmessage').call(this, wrappedHandler);
        }
      });
      
      // Also intercept addEventListener for 'message' events
      const originalAddEventListener = this.addEventListener;
      this.addEventListener = function(type, listener, ...args) {
        if (type === 'message') {
          const wrappedListener = (event) => {
            try {
              const data = event.data;
              if (typeof data === 'string') {
                window.dispatchEvent(new CustomEvent('GMGN_WS_INTERCEPT', {
                  detail: data
                }));
              }
            } catch (e) {
              console.error('[GMGN Monitor] Intercept error:', e);
            }
            // Call original listener
            if (listener) {
              listener.call(this, event);
            }
          };
          return originalAddEventListener.call(this, type, wrappedListener, ...args);
        }
        return originalAddEventListener.call(this, type, listener, ...args);
      };
    }
  }

  // Override globally
  window.WebSocket = InterceptedWebSocket;
  window._GMGN_MONITOR_PATCHED = true;
  
  console.log('[GMGN Monitor] WebSocket interceptor injected successfully.');
  
  // Notify content script that injection succeeded
  window.dispatchEvent(new CustomEvent('GMGN_INJECTOR_READY'));
})();

