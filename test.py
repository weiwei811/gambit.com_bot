from src.setup_driver import init_driver
from src.enter import enter_game
from src.get_data import read_bot_game
driver=init_driver()


# enter_game(driver,"bot_game")
print(read_bot_game(driver))