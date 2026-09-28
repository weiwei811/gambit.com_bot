import sys
from selenium.webdriver.common.keys import Keys
from src.strategy import sim_runs
from src.dataclass import Board
from src.enter import wait_until_element


def decision(board: Board) -> str:
    me = board.get_me()
    if not me:
        return "fold"

    # 取得當前模擬勝率
    winrate = sim_runs(board, 100)
    
    call_amount = me.call_amount or 0
    pot_size = board.pot
    
    # 如果可以過牌（免費看牌），且勝率不高，優先過牌
    if call_amount == 0:
        if winrate > 0.6: # 極大優勢，主動加注
             if me.min_to is not None:
                 return f"raise_{me.min_to}"
        return "check"

    # 計算底池賠率
    pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 1.0

    # 根據 EV 進行決策
    if winrate > pot_odds * 1.3: # 勝率遠大於賠率，考慮加注
        if me.min_to is not None and me.max_to is not None:
            # 避免像目前程式碼只加注中間值，可改為加注底池的特定比例 (如 1/2 pot)
            raise_amount = min(me.max_to, max(me.min_to, int(pot_size * 0.5)))
            return f"raise_{raise_amount}"
        return "call"
    
    elif winrate >= pot_odds: # 勝率略大於/等於賠率，跟注
        return "call"
        
    else: # 勝率小於賠率，長期虧損
        return "fold"


def exec_deci(driver, board: Board, action: str):
    """
    Executes the given decision in the browser via Selenium.
    """
    if not action:
        return

    if action == "fold":
        try:
            fold_button = wait_until_element(driver, "//*[text()='Fold']", timeout=3)
            fold_button.click()
        except Exception as e:
            print(f"Failed to click Fold: {e}")

    elif action == "check":
        try:
            check_button = wait_until_element(driver, "//*[text()='Check']", timeout=3)
            check_button.click()
        except Exception as e:
            print(f"Failed to click Check: {e}")

    elif action == "call":
        try:
            call_button = wait_until_element(driver, "//*[contains(text(), 'Call')]", timeout=3)
            call_button.click()
        except Exception as e:
            print(f"Failed to click Call: {e}")

    elif action.startswith("raise_"):
        amount = action.split("_")[1]
        try:
            raise_blank = wait_until_element(driver, "//input", timeout=3)
            select_all_key = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL
            raise_blank.send_keys(select_all_key, "a")
            raise_blank.send_keys(Keys.BACK_SPACE)
            raise_blank.send_keys(str(amount))

            try:
                raise_button = wait_until_element(driver, "//*[contains(text(), 'Raise')]", timeout=2)
                raise_button.click()
            except Exception:
                bet_button = wait_until_element(driver, "//*[contains(text(), 'Bet')]", timeout=2)
                bet_button.click()
        except Exception as e:
            print(f"Failed to execute raise: {e}")
