from dataclasses import dataclass, field
from typing import Optional
from random import choice
from src.classify_hand import classify_hand

RANK_MAP = {"T": 10, "J": 11, "Q": 12, "K": 13, "A": 1}


@dataclass
class Player:
    name: str = ""
    stack: int = 0
    seat: int = 0
    is_me: bool = False
    is_dealer: bool = False
    is_sb: bool = False
    is_bb: bool = False
    is_bot: bool = False
    rating: int = 0
    is_fold: bool = False
    is_turn: bool = False
    bet: int = 0
    hand: list = field(default_factory=list)
    all_in: Optional[int] = None
    max_to: Optional[int] = None
    min_to: Optional[int] = None
    call_amount: Optional[int] = None
    can_check: Optional[bool] = None
    can_call: Optional[bool] = None
    can_fold: Optional[bool] = None

    # Backwards-compatible properties
    @property
    def is_Turn(self) -> bool:
        return self.is_turn

    @is_Turn.setter
    def is_Turn(self, value: bool):
        self.is_turn = value

    @property
    def is_Dealer(self) -> bool:
        return self.is_dealer

    @is_Dealer.setter
    def is_Dealer(self, value: bool):
        self.is_dealer = value

    @property
    def is_SB(self) -> bool:
        return self.is_sb

    @is_SB.setter
    def is_SB(self, value: bool):
        self.is_sb = value

    @property
    def is_BB(self) -> bool:
        return self.is_bb

    @is_BB.setter
    def is_BB(self, value: bool):
        self.is_bb = value

    @property
    def is_Bot(self) -> bool:
        return self.is_bot

    @is_Bot.setter
    def is_Bot(self, value: bool):
        self.is_bot = value

    @property
    def maxTo(self) -> Optional[int]:
        return self.max_to

    @maxTo.setter
    def maxTo(self, value: Optional[int]):
        self.max_to = value

    @property
    def minTo(self) -> Optional[int]:
        return self.min_to

    @minTo.setter
    def minTo(self, value: Optional[int]):
        self.min_to = value

    @property
    def allIn(self) -> Optional[int]:
        return self.all_in

    @allIn.setter
    def allIn(self, value: Optional[int]):
        self.all_in = value

    @property
    def call(self) -> Optional[int]:
        return self.call_amount

    @call.setter
    def call(self, value: Optional[int]):
        self.call_amount = value

    def __repr__(self) -> str:
        return f"Player(name='{self.name}', stack={self.stack}, seat={self.seat}, hand={self.hand})"


@dataclass
class Board:
    players: list[Player] = field(default_factory=list)
    public_cards: list = field(default_factory=list)
    pot: int = 0
    allowed: dict = field(default_factory=dict)
    street: str = "preflop"

    def get_me(self) -> Optional[Player]:
        for player in self.players:
            if player.is_me:
                return player
        return None

    def get_dealer(self) -> Optional[Player]:
        for player in self.players:
            if player.is_dealer:
                return player
        return None

    def remain(self) -> set:
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

    def remain_player_count(self) -> int:
        return sum(1 for player in self.players if not player.is_fold)

    def get_winners(self):
        active_players = [p for p in self.players if not p.is_fold]
        if not active_players:
            return []

        # 僅剩一人未蓋牌時直接獲勝
        if len(active_players) == 1:
            return active_players

        # 攤牌階段必須有五張公共牌
        if len(self.public_cards) < 5:
            return None

        for player in active_players:
            if len(player.hand) < 2:
                return None

        player_scores = []
        for player in active_players:
            best_combo = classify_hand(player.hand + self.public_cards)
            player_scores.append((player, best_combo))

        max_score = max(score for _, score in player_scores)
        winners = [player for player, score in player_scores if score == max_score]
        return winners

    def __repr__(self) -> str:
        return f"Board(players={len(self.players)}, public_cards={self.public_cards}, pot={self.pot})"


def card_correct(raw_cards) -> list:
    """
    Normalizes cards from string representations (e.g. 'Ts', '10s', 'Ah') or tuples
    into (rank_int, suit_str) where Ace is 1 and 10 is 10.
    """
    if not raw_cards:
        return []

    cards = []
    for card in raw_cards:
        if isinstance(card, (tuple, list)):
            cards.append(tuple(card))
            continue
        if not isinstance(card, str) or len(card) < 2:
            continue
        rank_str = card[:-1]
        suit = card[-1].lower()
        rank = int(RANK_MAP.get(rank_str.upper(), rank_str))
        cards.append((rank, suit))
    return cards


def data2board(data: dict) -> Board:
    board = Board()
    if not data or not isinstance(data, dict):
        return board

    hero_seat = data.get("heroSeat")
    if hero_seat is not None:
        hero_seat = int(hero_seat)
    allowed = data.get("allowed") or {}

    for player in data.get("players", []):
        seat = int(player.get("seat", 0))
        # Use heroSeat if available, fallback to checking if cards are present
        if hero_seat is not None:
            is_me = (seat == hero_seat)
        else:
            is_me = (player.get("cards") is not None)

        pl = Player(
            name=player.get("name", ""),
            stack=player.get("stack", 0),
            seat=seat,
            is_me=is_me,
            is_dealer=bool(player.get("isDealer")),
            is_sb=bool(player.get("isSB")),
            is_bb=bool(player.get("isBB")),
            is_bot=bool(player.get("isBot")),
            rating=player.get("rating", 0),
            is_fold=(player.get("status") == "folded"),
            is_turn=bool(player.get("isTurn")),
            bet=player.get("bet", 0),
        )

        # Populate hand whenever cards are available for the player (especially hero)
        if player.get("cards"):
            pl.hand = card_correct(player["cards"])

        # Populate allowed action metadata for hero on hero's turn
        if pl.is_me and pl.is_turn and allowed:
            pl.all_in = allowed.get("allIn")
            bet_raise = allowed.get("betRaise") or {}
            pl.max_to = bet_raise.get("maxTo")
            pl.min_to = bet_raise.get("minTo")
            pl.call_amount = allowed.get("call")
            pl.can_check = bool(allowed.get("check"))
            pl.can_call = bool(allowed.get("call") is not None and allowed.get("call") is not False)
            pl.can_fold = bool(allowed.get("fold"))

        board.players.append(pl)

    board.public_cards = card_correct(data.get("board"))
    board.pot = data.get("pot", 0)
    board.allowed = allowed
    board.street = data.get("street", "preflop")
    return board
