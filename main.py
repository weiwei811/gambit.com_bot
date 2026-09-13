from src.setup_driver import init_driver
from src.enter import reset,login,enter_game
from src.get_data import get_game_data
from src.dataclass import data2board
from src.play import decision
from time import sleep
import json
from src.play import exec_deci
def main():
    driver=init_driver()
    reset(driver)
    login(driver)
    enter_game(driver,"bot_game")

    while True:
        data=get_game_data(driver)
        print("data",json.dumps(data,indent=3))
        if data["players"] == []:
            sleep(1)
            continue
        board=data2board(data)
        me=board.get_me()
        if me.is_Turn:
            deci=decision(board)
            print("deci",deci)
            exec_deci(driver,board,deci)
        sleep(1)

    input()

main()