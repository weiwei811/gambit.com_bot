from copy import deepcopy

def fill_board(board):
    for player in board.players:
        while len(player.hand)<2 and not player.is_fold:
            player.hand.append(board.deal())
    while len(board.public_cards)<5:
        board.public_cards.append(board.deal())

def sim_game(board):
    clone=deepcopy(board)
    # fill
    fill_board(clone)
    # win/lose
    winner=clone.winner()
    return winner.is_me

def sim_runs(board,n):
    win=0
    for _ in range(n):
        result=sim_game(board)
        if result:
            win+=1
    me=board.get_me()
    bet=me.bet
    pot=board.pot
    P_win=win/n
    P_lose=1-P_win
    ev=P_win*pot-P_lose*bet
    return ev


        