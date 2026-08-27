from selenium import webdriver
from src.strategy import sim_runs
from src.dataclass import Board
from src.enter import wait_until_element


def decision(board:Board):
    alive=board.remain_player_count()
    winrate=sim_runs(board,100)
    print(winrate)
    me=board.get_me()
    bet=me.bet
    pot=board.pot
    P_win=winrate
    P_lose=1-P_win
    ev=P_win*pot-P_lose*bet
    if winrate<=1/alive:
        return "fold or check"
    elif winrate<=1.3/alive:
        return "call"
    else:
        return "raise"
    
def exec_deci(driver,board:Board,decision):

    me=board.get_me()
    if decision=="fold or check":
        if me.can_check:
            pass
        else:
            print("try to fold")
            fold_button=wait_until_element(driver,"/html/body/div[1]/div/div/div/div/div[2]/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div[5]/div/div[2]/div[1]")
            fold_button.click()






