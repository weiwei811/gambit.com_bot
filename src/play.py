from src.dataclass import Board
from src.ai_decision import decision
from src.game_controls import click_action, set_raise_amount

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
            set_raise_amount(driver, amount)
            click_action(driver, "raise", "bet", "all_in", expected_amount=amount)
        except Exception as e:
            print(f"Failed to execute raise ({type(e).__name__}): {e}")
