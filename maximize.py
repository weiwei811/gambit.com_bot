def maximize(board,last_move="")
    if len(board.public_cards)==5 or last_move=="fold":
        return expectation(board,last_move)  
    all_cards=[a+]
    maxExp=-float("inf")
    maxMove=""
    available_moves=["continue","fold"]
    public_cards=board.public_cards
    remainingcard=all_cards-my_cards-public_cards # TODO

    for move in available_moves:
        move_exp=0
        for card in remaining_card:
            # TODO prepare next board(add tested card)
            next_board=Board()
            # END TODO
            eval,_=maximize(next_board,last_move=move)
            move_exp+=1/len(remaining_card)*eval
            
        if move_exp>maxExp:
            maxExp=move_exp
            maxMove=move

    return maxEval,move

def expectation(board,last_move): # TODO
    if last_move=="fold":
        return  # TODO should be positive
    all_cards=board.myplayer.cards+board.public_cards
    best=best_combine(all_cards)
    score={"house":50,"full_house":70,"pair":20} #TODO
    return score[best]