from selenium import webdriver
import os
from time import sleep
def init_driver():
    options= webdriver.ChromeOptions()
    options.debugger_address="127.0.0.1:9222"
    print("connecting")
    try:
        driver = webdriver.Chrome(options=options)
    except:
        os.system('"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-selenium"')
        sleep(2)
        driver = webdriver.Chrome(options=options)
    print("created")
    setup_network_interceptor(driver)
    return driver

def setup_network_interceptor(driver):
    """
    Injects a JavaScript hook to intercept WebSocket, Fetch, and XHR traffic.
    Broadened to capture both multiplayer tournaments and solo bot games.
    """

    js_hook = """
    if (!window.__network_hooked) {
        window.__GAMBIT_BOARD_STATE = null;
        
        // Helper function to check if the payload resembles a game state
        function isGameData(data) {
            if (!data || typeof data !== 'object') return false;
            const str = JSON.stringify(data).toLowerCase();
            
            // Expanded keywords to catch bot matches (which may lack tableId)
            const keywords = ['phase', 'hand', 'cards', 'board', 'snapshot', 'dealer', 'wager', 'pot'];
            return keywords.some(keyword => str.includes(keyword));
        }

        // --- 1. WEBSOCKET INTERCEPTOR ---
        const NativeWebSocket = window.WebSocket;
        window.WebSocket = function(url, protocols) {
            const ws = new NativeWebSocket(url, protocols);
            ws.addEventListener('message', function(event) {
                try {
                    let data = JSON.parse(event.data);
                    // Unwrap Socket.io style arrays if necessary
                    if (Array.isArray(data)) {
                        data = data.find(item => typeof item === 'object' && item !== null);
                    }
                    if (isGameData(data)) {
                        window.__GAMBIT_BOARD_STATE = data;
                    }
                } catch(e) {
                    // Fallback for custom string prefixes
                    if (typeof event.data === 'string') {
                        const match = event.data.match(/({.*})/);
                        if (match) {
                            try {
                                const parsed = JSON.parse(match[1]);
                                if (isGameData(parsed)) {
                                    window.__GAMBIT_BOARD_STATE = parsed;
                                }
                            } catch(err) {}
                        }
                    }
                }
            });
            return ws;
        };
        
        window.WebSocket.prototype = NativeWebSocket.prototype;
        window.WebSocket.CONNECTING = NativeWebSocket.CONNECTING;
        window.WebSocket.OPEN = NativeWebSocket.OPEN;
        window.WebSocket.CLOSING = NativeWebSocket.CLOSING;
        window.WebSocket.CLOSED = NativeWebSocket.CLOSED;

        // --- 2. FETCH API INTERCEPTOR (For Modern Bot Games) ---
        const originalFetch = window.fetch;
        window.fetch = async function() {
            const response = await originalFetch.apply(this, arguments);
            try {
                // Clone the response so the game can still read the original stream
                const clone = response.clone();
                clone.text().then(text => {
                    try {
                        const data = JSON.parse(text);
                        if (isGameData(data)) {
                            window.__GAMBIT_BOARD_STATE = data;
                        }
                    } catch(e) {}
                });
            } catch(e) {} // Ignore clone/stream reading errors
            return response;
        };

        // --- 3. XHR (AJAX) INTERCEPTOR (For Legacy Bot Games) ---
        const originalXHROpen = window.XMLHttpRequest.prototype.open;
        window.XMLHttpRequest.prototype.open = function() {
            this.addEventListener('load', function() {
                try {
                    const data = JSON.parse(this.responseText);
                    if (isGameData(data)) {
                        window.__GAMBIT_BOARD_STATE = data;
                    }
                } catch(e) {}
            });
            return originalXHROpen.apply(this, arguments);
        };
        
        window.__network_hooked = true;
    }
    """
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js_hook})

