import sys
from selenium.webdriver.common.keys import Keys
from src.dataclass import Board
from src.enter import wait_until_element
from src.ai_decision import decision
from src.game_controls import click_action

def exec_deci(driver, board: Board, action: str):
    """
    Executes the given decision in the browser via Selenium.
    """
    if not action:
        return

    if action == "fold":
        try:
            click_action(driver, "fold")
        except Exception as e:
            print(f"Failed to click Fold: {e}")

    elif action == "check":
        try:
            click_action(driver, "check")
        except Exception as e:
            print(f"Failed to click Check: {e}")

    elif action == "call":
        try:
            click_action(driver, "call")
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

            click_action(driver, "raise", "bet")
        except Exception as e:
            print(f"Failed to execute raise: {e}")
