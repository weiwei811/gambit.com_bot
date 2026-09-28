import json
import random
from src.setup_driver import init_driver
from src.enter import reset, login, enter_game
from src.get_data import get_game_data
from src.dataclass import Board, Player, data2board
from src.strategy import sim_runs
from src.play import decision, exec_deci
from src.classify_hand import classify_5
from src.analysis import analyze

if __name__ == "__main__":
    random.seed(33)
    # Quick sanity test of analysis
    analyze(50)

    # Browser test scaffold (commented out by default):
    # driver = init_driver()
    # reset(driver)
    # login(driver)
    # enter_game(driver, "bot_game")
    # data = get_game_data(driver)
    # board = data2board(data)
    # print("Parsed board:", board)
    # print("Decision:", decision(board))
