from selenium import webdriver
from src.strategy import sim_runs

def decision(board):
    ev=sim_runs(board,1000)
    if ev<=0:
        return "fold"
    elif 0<ev<=0.5:
        return "call"
    elif ev/board.pot>0.5:
        return "raise"
    
def exec_deci():
    pass



