from dataclasses import dataclass, field
from src.classify_hand import classify_hand
from random import choice

@dataclass
class Player:
    name: str = ""
    balance: int = 0
    init_balance: int = 200
    bet: int = 0
    is_dealer: bool = False
    is_fold: bool = False
    rating: int = 0
    pos: list = field(default_factory=list)
    is_me: bool = False
    hand: list = field(default_factory=list)


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
        

