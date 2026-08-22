from src.setup_driver import init_driver
from src.enter import reset,login,enter_game
from src.get_data import get_game_data

def main():
    driver=init_driver()
    reset(driver)
    login(driver)
    enter_game("bot_game",driver)
    while True:
        data=get_game_data(driver)
        board=data2board(data)
        decision=decide(board)
        exec_decision(decision)

    input()

main()