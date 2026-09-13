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
    # print("public_cards",clone.public_cards)
    winner=clone.winner()
    return winner.is_me

def sim_runs(board,n):
    win=0
    # print(board)
    for _ in range(n):
        result=sim_game(board)
        if result:
            win+=1
        # print(result)
    winrate=win/n

    return winrate



        