from selenium.webdriver.common.keys import Keys
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
        if me.can_check:
            return "check"
        elif me.can_fold:
            return "fold"
    elif winrate<=1.3/alive:
        if me.can_call:
            return "call"
        else:
            return "check"
    else:
        return "raise_(me.maxTo+me.minTo)//2" #TODO
    
def exec_deci(driver,board:Board,decision):

    me=board.get_me()
    if decision=="fold":
        fold_button=wait_until_element(driver,"//*[text()='Fold']")
        fold_button.click()
    elif decision=="check":
        check_button=wait_until_element(driver,"//*[text()='Check']")
        check_button.click()
    elif decision=="call":
        call_button=wait_until_element(driver,"//*[contains(text(), 'Call:')]")
        call_button.click()
    else:
        raise_blank=wait_until_element(driver,"//input")
        raise_blank.send_keys(Keys.BACK_SPACE)
        raise_blank.send_keys(f"{decision.split('_')[1]}")
        try: #TODO
            raise_button=wait_until_element(driver,"//*[contains(text(), 'Raise:')]")
            raise_button.click()
        except:
            bet_button=wait_until_element(driver,"//*[contains(text(), 'Bet:')]")
            bet_button.click()








