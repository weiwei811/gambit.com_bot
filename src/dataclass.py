from dataclasses import dataclass, field
from src.classify_hand import classify_hand
from random import choice

@dataclass
class Player:
    name: str = ""
    stack: int = 0
    seat: int = 0
    is_me: bool = False
    is_Dealer: bool = False
    is_SB: bool = False
    is_BB: bool = False
    is_Bot: bool = False
    rating: int = 0
    is_fold: bool = False
    is_Turn: bool = False
    bet: int = 0
    hand: list = field(default_factory=list)
    allIn: int = None
    maxTo: int = None
    minTo: int = None
    call: int = None
    can_check: bool = None
    can_call: bool = None
    can_fold: bool = None
    def __repl__(self):
        s=f"{self.name},{self.stack},{self.seat},{self.hand}"
        return s

@dataclass
class Board:
    players: list[Player] = field(default_factory=list)
    public_cards: list = field(default_factory=list)
    pot: int = 0

    def get_me(self):
        for player in self.players:
            if player.is_me:
                return player
        return None

    def remain(self):
        remaining = {
            (num, suit)
            for num in range(1, 14)
            for suit in ["s", "h", "c", "d"]
        }

        for player in self.players:
            for card in player.hand:
                remaining.discard(card)

        for card in self.public_cards:
            remaining.discard(card)

        return remaining

    def deal(self):
        remaining = self.remain()

        if not remaining:
            return None

        return choice(list(remaining))
    def remain_player_count(self):
        alive=0
        for player in self.players:
            if not player.is_fold:
                alive+=1
        return alive
    def winner(self):
        # 每個仍參與牌局的玩家必須有兩張牌
        for player in self.players:
            if player.is_fold:
                continue

            if len(player.hand) < 2:
                return None

        # 必須有五張公共牌
        if len(self.public_cards) < 5:
            return None

        winner = None
        winner_hand = None

        for player in self.players:
            if player.is_fold:
                continue

            combo = classify_hand(
                player.hand + self.public_cards
            )

            if winner_hand is None:
                winner = player
                winner_hand = combo
                continue

            if combo[0] > winner_hand[0]:
                winner = player
                winner_hand = combo

            elif combo[0] == winner_hand[0]:
                if combo[1] > winner_hand[1]:
                    winner = player
                    winner_hand = combo

        return winner
    
    def get_dealer(game): ## TODO
        players = game["players"]
        dealer = next(
            (
                player
                for player in players
                if player.get("isDealer") is True
            ),
            None,
        )
        return dealer
    def __repl__(self):
        s=f"{self.players},{self.public_cards},{self.pot}"
        return s
def card_correct(wrong):
    print("card corection",wrong)
    cards=[]
    for card in wrong:
        suit2num={"T":10,"J":11,"Q":12,"K":13,"A":1}
        cards.append((int(suit2num.get(card[0],card[0])),card[-1]))
    return cards
    
    
def data2board(data):
    board=Board()
    for player in data["players"]:
        pl=Player(name=player["name"],
                  stack=player["stack"],
                  seat=player["seat"],
                  is_me=(player["cards"] != None),
                  is_Dealer=player["isDealer"],
                  is_SB=player["isSB"],
                  is_BB=player["isBB"],
                  is_Bot=player["isBot"],
                  rating=player["rating"],
                  is_fold=(player["status"] == "folded"),
                  is_Turn=player["isTurn"],
                  bet=player["bet"],
                  )
        if pl.is_me and pl.is_Turn:
            pl.hand=card_correct(player["cards"])
            pl.allIn=data["allowed"]["allIn"]
            pl.maxTo=data["allowed"]["betRaise"]["maxTo"]
            pl.minTo=data["allowed"]["betRaise"]["minTo"]
            pl.call=data["allowed"]["call"]
            pl.can_check=data["allowed"]["check"]
            pl.can_call=data["allowed"]["call"]
            pl.can_fold=data["allowed"]["fold"]
                
        board.players.append(pl)
    board.public_cards=card_correct(data["board"])
    if not board.public_cards:
        board.public_cards=[]
    board.pot=data["pot"]
    return(board)

