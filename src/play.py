import sys
from selenium.webdriver.common.keys import Keys
from src.dataclass import Board
from src.enter import wait_until_element
from src.ai_decision import decision

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
