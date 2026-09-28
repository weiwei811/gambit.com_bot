import random
from src.classify_hand import classify_hand

FULL_DECK = [(num, suit) for num in range(1, 14) for suit in ["s", "h", "c", "d"]]


def fast_monte_carlo(hero_hand: list, public_cards: list, opp_hands: list, n: int = 100) -> float:
    """
    High-performance Monte Carlo simulation for poker hand equity.
    Avoids deepcopy and UI allocations by working directly with card tuples.
    Correctly handles ties (split pots) by awarding fractional equity.
    """
    known = set(hero_hand + public_cards)
    for h in opp_hands:
        known.update(h)

    deck = [c for c in FULL_DECK if c not in known]
    cards_for_board = 5 - len(public_cards)
    opps_needing_cards = [2 - len(h) for h in opp_hands]
    total_needed = cards_for_board + sum(opps_needing_cards)

    if total_needed > len(deck):
        return 0.0

    wins = 0.0
    for _ in range(n):
        sampled = random.sample(deck, total_needed)
        curr_board = public_cards + sampled[:cards_for_board]
        hero_score = classify_hand(hero_hand + curr_board)

        idx = cards_for_board
        hero_won = True
        split_count = 1

        for i, h in enumerate(opp_hands):
            need = opps_needing_cards[i]
            opp_full_hand = h + sampled[idx:idx + need]
            idx += need
            opp_score = classify_hand(opp_full_hand + curr_board)

            if opp_score > hero_score:
                hero_won = False
                break
            elif opp_score == hero_score:
                split_count += 1

        if hero_won:
            wins += 1.0 / split_count

    return wins / n


def sim_runs(board, n: int = 100) -> float:
    """Simulates n showdowns for the given board state and returns hero's equity."""
    hero = board.get_me()
    if not hero or len(hero.hand) < 2:
        return 0.0

    active_opponents = [p for p in board.players if not p.is_me and not p.is_fold]
    if not active_opponents:
        return 1.0

    return fast_monte_carlo(
        hero_hand=hero.hand,
        public_cards=board.public_cards,
        opp_hands=[p.hand for p in active_opponents],
        n=n,
    )


def sim_game(board) -> bool:
    """Simulates a single showdown and returns whether hero won or tied."""
    return sim_runs(board, n=1) > 0.0


def fill_board(board):
    """Helper to populate missing cards for offline mock boards."""
    for player in board.players:
        while len(player.hand) < 2 and not player.is_fold:
            card = board.deal()
            if not card:
                break
            player.hand.append(card)
    while len(board.public_cards) < 5:
        card = board.deal()
        if not card:
            break
        board.public_cards.append(card)