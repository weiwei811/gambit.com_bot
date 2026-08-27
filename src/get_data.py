from src.dataclass import Board, Player
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


def get_board(driver):
    """
    Retrieves the most recent game snapshot captured by the network interceptor.
    """
    board_state = driver.execute_script("return window.__GAMBIT_BOARD_STATE || null;")
    return board_state


def get_game_data(driver):

    return driver.execute_script("""
        if (typeof globalThis.__r !== "function") {
            return {
                ready: false,
                error: "__r is unavailable"
            };
        }

        function findModule(predicate, knownIds) {
            for (const id of knownIds) {
                try {
                    const m = globalThis.__r(id);
                    if (m && predicate(m)) return m;
                } catch (_) { /* unknown module */ }
            }
            for (let id = 300; id <= 8000; id++) {
                try {
                    const m = globalThis.__r(id);
                    if (m && predicate(m)) return m;
                } catch (_) { /* unknown module */ }
            }
            return null;
        }

        function looksLikeStore(s) {
            return s && typeof s.getState === "function";
        }

        const sessionManager = findModule(
            (m) =>
                typeof m.getSession === "function" &&
                typeof m.useSessionRegistry === "function" &&
                typeof m.getOrCreateSession === "function",
            [2033]
        );

        const gameStoreModule = findModule(
            (m) => looksLikeStore(m.defaultGameStore) || looksLikeStore(m.useGameStore),
            [1570]
        );

        let store = null;
        let sessionKey = null;
        let registryKeys = [];

        if (sessionManager) {
            const registry = sessionManager.useSessionRegistry;
            const sessions = registry.getState().sessions || {};
            registryKeys = Object.keys(sessions);

            let bestScore = -1;
            for (const key of registryKeys) {
                const s = sessions[key];
                if (!s || s.retired) continue;

                let score = 0;
                if (s.isConnected) score += 100;
                if (s.status === "active") score += 50;
                if (s.format === "bots") score += 10;
                if (s.isSeated) score += 20;

                const session = sessionManager.getSession(key);
                const hasSnapshot = Boolean(
                    session &&
                    session.store &&
                    session.store.getState &&
                    session.store.getState().snapshot
                );
                if (hasSnapshot) score += 1000;

                if (score > bestScore) {
                    bestScore = score;
                    sessionKey = key;
                }
            }

            if (sessionKey) {
                const session = sessionManager.getSession(sessionKey);
                store = session && session.store;
            }
        }

        if (!looksLikeStore(store) && gameStoreModule) {
            store = gameStoreModule.defaultGameStore || gameStoreModule.useGameStore;
        }

        if (!looksLikeStore(store)) {
            return {
                ready: false,
                error: "active game store unavailable",
                sessionKey,
                registryKeys
            };
        }

        const state = store.getState();
        const snapshot = state.snapshot;

        return {
            ready: Boolean(
                snapshot &&
                Array.isArray(snapshot.seats)
            ),

            sessionKey: sessionKey ?? null,
            activeConnectionId: state.activeConnectionId ?? null,
            isConnected: state.isConnected ?? false,
            handId: state.handId ?? snapshot?.handId ?? null,

            players: snapshot?.seats ?? state.seats ?? [],
            board: snapshot?.board ?? state.board ?? [],
            pot: snapshot?.pot ?? state.pot ?? 0,
            street: snapshot?.street ?? state.currentStreet ?? null,
            heroSeat: snapshot?.heroSeat ?? state.heroSeat ?? null,
            allowed: snapshot?.allowed ?? state.allowed ?? null,

            snapshotKeys: snapshot
                ? Object.keys(snapshot)
                : []
        };
    """)
def get_board_state(driver):
    board=Board()
    elements = driver.find_elements(By.CSS_SELECTOR, "[class='css-g5y9jx r-1awozwy r-u8s1d r-wc24c3 r-12vffkv']")
    for element in elements:
        player=Player()
        try:
            balance=element.find_element(By.CSS_SELECTOR,"[class='css-146c3p1 r-jwli3a r-1qe02qc r-14yzgew r-1mnahxq r-iqz8a4 r-n6v787']")
            player.balance=int(balance.text)
        except NoSuchElementException:
            balance=element.find_element(By.CSS_SELECTOR,"[class='css-146c3p1 r-1qe02qc r-14yzgew r-1mnahxq r-iqz8a4 r-n6v787 r-cosyor']")
            player.balance=int(balance.text)
            player.is_fold=True

        name=element.find_element(By.CSS_SELECTOR,"[class='css-146c3p1 r-1udh08x r-1udbk01 r-3s2u2q r-1iln25a r-1kihuf0 r-116b78n r-1ldl6ut r-q4m81j r-1enofrn r-1f529hi r-15zivkp r-kc8jnq r-1jizoa0']")
        player.name=name.text
        player.bet=player.init_balance-player.balance
        style=element.get_attribute("style").split("; ")
        styles={}
        for s  in style:
            key,val=s.split(": ")
            styles[key]=val
        player.pos=[float(styles["top"][:-2]),float(styles["left"][:-2])]
        print(player)
        board.players.append(element)
    pot=element.find
