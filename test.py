from src.setup_driver import init_driver
from src.enter import *
from src.get_data import get_game_data
from src.dataclass import data2board
from src.strategy import sim_runs
import json
from src.play import decision,exec_deci
from src.classify_hand import classify_5


# driver=init_driver()
# # reset(driver)
# # login(driver)
# # enter_game(driver,"bot_game")
# data=get_game_data(driver)
# board=data2board(data)
# # print(decision(board))
# # print(data)

# # print(classify_5(((12, 's'), (10, 's'), (1, 's'), (13, 's'), (11, 's'))))

# # print(json.dumps(get_game_data(driver),indent=3))

# exec_deci(driver,board,"call")
# # board=data2board(data)
