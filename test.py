from src.setup_driver import init_driver
from src.enter import enter_game
from src.get_data import get_game_data
from src.dataclass import data2board
import json
driver=init_driver()


# enter_game(driver,"bot_game")
print(json.dumps(get_game_data(driver),indent=3))
data=get_game_data(driver)
board=data2board(data)