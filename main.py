import json
from time import sleep
from src.setup_driver import init_driver
from src.enter import reset, login, enter_game
from src.get_data import get_game_data
from src.dataclass import data2board
from src.play import decision, exec_deci


def main():
    driver = init_driver()
    reset(driver)
    login(driver)
    enter_game(driver, "bot_game")

    try:
        while True:
            data = get_game_data(driver)
            if not data or not data.get("ready") or not data.get("players"):
                sleep(1)
                continue

            board = data2board(data)
            me = board.get_me()
            if me and me.is_turn:
                deci = decision(board)
                print(f"Action chosen: {deci}")
                exec_deci(driver, board, deci)

            sleep(1)
    except KeyboardInterrupt:
        print("\nBot stopped by user.")


if __name__ == "__main__":
    main()