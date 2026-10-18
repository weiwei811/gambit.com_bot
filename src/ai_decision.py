"""Inference adapter for the six-player Alpha Hold'em policy.

The model was trained with the vendored Alpha Hold'em observation layout. This
module recreates that layout from the public snapshots consumed by main.py.
"""
from __future__ import annotations

import pickle
import os
from pathlib import Path

import numpy as np
import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "six_player_best_2026-10-06.pkl"
NUM_PLAYERS = 6
HISTORY_PER_STREET = 20
ACTION_COUNT = 5
ACTION_IDS = {"fold": 0, "check_call": 1, "raise_half_pot": 2, "raise_pot": 3, "all_in": 4}
STREETS = {"preflop": 0, "pre-flop": 0, "flop": 1, "turn": 2, "river": 3}
SUITS = {"c": 0, "d": 1, "h": 2, "s": 3}
RANKS = {rank: i for i, rank in enumerate("23456789TJQKA")}


class ResBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride, 1)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, 1, 1)
        self.relu2 = nn.ReLU()
        self.shortcut = (nn.Conv2d(in_channels, out_channels, 1, stride)
                         if stride > 1 or in_channels != out_channels else nn.Identity())

    def forward(self, x):
        return self.relu2(self.conv2(self.relu1(self.conv1(x))) + self.shortcut(x))


class Slim(nn.Module):
    """Match RLlib SlimFC parameter names in the published checkpoint."""
    def __init__(self, in_features, out_features, activation=None):
        super().__init__()
        self._model = nn.Sequential(nn.Linear(in_features, out_features))
        self.activation = nn.ReLU() if activation else nn.Identity()

    def forward(self, x):
        return self.activation(self._model(x))


class FeatureEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.cards = nn.Sequential(ResBlock(6, 16, 1), ResBlock(16, 32, 2), ResBlock(32, 64, 2))
        self.actions = nn.Sequential(ResBlock(81, 16, 1), ResBlock(16, 32, 2), ResBlock(32, 64, 2))
        self.public = Slim(48, 32, True)
        self.fuse = nn.Sequential(Slim(544, 256, True), Slim(256, 128, True), Slim(128, 64, True))

    def forward(self, obs):
        table = obs["table_info"].clone()
        table[:, :, 0] /= 200.0
        betting = obs["betting_info"].clone()
        betting[:, :6] /= 200.0
        betting[:, 7] = torch.log1p(betting[:, 7])
        betting[:, 8] /= max(NUM_PLAYERS - 1, 1)
        betting[:, 9] /= 3.0
        extra = torch.cat((obs["extra_info"] / 200.0, table.flatten(1), betting), dim=1)
        cards = self.cards(obs["card_info"].permute(0, 3, 1, 2).float()).flatten(1)
        actions = self.actions(obs["action_info"].permute(0, 3, 1, 2).float()).flatten(1)
        return self.fuse(torch.cat((cards, actions, self.public(extra)), dim=1))


class Policy(nn.Module):
    def __init__(self):
        super().__init__()
        self.policy_encoder = FeatureEncoder()
        self.value_encoder = FeatureEncoder()
        self.policy_head = Slim(64, ACTION_COUNT)
        self.value_head = Slim(64, 1)

    def forward(self, obs):
        return self.policy_head(self.policy_encoder(obs))


def _card(card):
    if isinstance(card, (tuple, list)) and len(card) == 2:
        rank, suit = card
        rank = int(rank)
        rank = 14 if rank == 1 else rank
        rank_token = "23456789TJQKA"[rank - 2] if 2 <= rank <= 14 else None
        return (SUITS.get(str(suit).lower()), RANKS.get(rank_token))
    if not isinstance(card, str) or len(card) < 2:
        return None
    token, suit = card[:-1].upper(), card[-1].lower()
    token = "T" if token in ("10", "T") else token
    return SUITS.get(suit), RANKS.get(token)


class GameHistory:
    """Reconstruct public per-street actions from successive game snapshots."""
    def __init__(self):
        self.hand_id = None
        self.previous = None
        self.history = [[], [], [], []]
        self.contributions = [0.0] * NUM_PLAYERS
        self.last_raise_amount = 2.0

    def observe(self, data):
        hand_id = data.get("handId")
        players = _seats(data)
        if len(players) != NUM_PLAYERS:
            # Let decision() use the legacy policy on unsupported tables.
            self.previous = None
            self.history = [[], [], [], []]
            self.contributions = [0.0] * NUM_PLAYERS
            return
        layout_changed = (self.previous is not None and
                          _seat_ids(players) != _seat_ids(_seats(self.previous)))
        if self.previous is None or layout_changed or (hand_id is not None and hand_id != self.hand_id):
            self.hand_id = hand_id
            self.previous = data
            self.history = [[], [], [], []]
            self.last_raise_amount = 2.0
            self.contributions = [0.0] * NUM_PLAYERS
            for index, player in enumerate(players):
                self.contributions[index] = float(player.get("bet") or 0)
            return
        old = self.previous
        if _street(old) != _street(data):
            self.last_raise_amount = 2.0
        old_players, new_players = _seats(old), _seats(data)
        actor_index = next((i for i, p in enumerate(old_players) if p.get("isTurn")), None)
        if actor_index is not None and len(old_players) == NUM_PLAYERS and len(new_players) == NUM_PLAYERS:
            old_street = _street(old)
            oldp, newp = old_players[actor_index], new_players[actor_index]
            actor = actor_index
            old_bet = float(oldp.get("bet") or 0)
            new_bet = float(newp.get("bet") or 0)
            old_status = str(oldp.get("status", "")).lower()
            new_status = str(newp.get("status", "")).lower()
            progressed = (not newp.get("isTurn") or old_street != _street(data) or
                          old.get("pot") != data.get("pot") or old_bet != new_bet or
                          old_status != new_status)
            if not progressed:
                self.previous = data
                return
            call = max(float((old.get("allowed") or {}).get("call") or 0), 0.0)
            delta = max(0.0, new_bet - old_bet)
            if old_status != "folded" and new_status == "folded":
                action = 0
            elif new_status in ("allin", "all_in", "all-in") or (
                    newp.get("stack") is not None and float(newp["stack"]) <= 0):
                action = 4
                self.contributions[actor] += max(delta, float((old.get("allowed") or {}).get("allIn") or 0))
            elif delta > 0:
                self.contributions[actor] += delta
                if delta <= call:
                    action = 1
                else:
                    amount = delta
                    pot = max(float(old.get("pot") or 0), 1.0)
                    half_pot = call + int((pot + call) * 0.5)
                    pot_raise = call + int(pot + call)
                    action = 2 if abs(amount - half_pot) <= abs(amount - pot_raise) else 3
                    self.last_raise_amount = max(1.0, delta - call)
            else:
                action = 1
                self.contributions[actor] += call
            allowed = _legal_actions(old.get("allowed") or {}, oldp)
            self.history[old_street].append((actor, action, allowed))
            self.history[old_street] = self.history[old_street][-HISTORY_PER_STREET:]
        self.previous = data


def _seats(data):
    # Stable numeric seat order is also the model's clockwise row order.
    # Keep external seat IDs in snapshots; only model/history rows are dense.
    players = data.get("players") or data.get("seats") or []
    return sorted(players, key=lambda p: int(p["seat"]))


def _seat_ids(players):
    return tuple(int(p["seat"]) for p in players)


def _street(data):
    if len(data.get("board") or []) >= 5:
        return 3
    if len(data.get("board") or []) == 4:
        return 2
    if len(data.get("board") or []) == 3:
        return 1
    return STREETS.get(str(data.get("street", "preflop")).lower(), 0)


def _legal_actions(allowed, player):
    legal = []
    if allowed.get("fold", True):
        legal.append(0)
    if allowed.get("check") or (allowed.get("call") is not None and allowed.get("call") is not False):
        legal.append(1)
    limits = allowed.get("betRaise") or {}
    if limits.get("minTo") is not None and limits.get("maxTo") is not None:
        legal.extend((2, 3))
    if allowed.get("allIn") not in (None, False, 0):
        legal.append(4)
    return sorted(set(legal or [0, 1]))


def _make_observation(board, history, contributions, last_raise_amount=2.0):
    players = sorted(board.players, key=lambda p: int(p.seat))
    if len(players) != NUM_PLAYERS:
        raise ValueError(f"The checkpoint requires exactly six seats; received {len(players)}")
    hero = board.get_me()
    if hero is None or len(hero.hand) != 2:
        raise ValueError("Hero hole cards are required for model inference")
    seat_to_index = {int(p.seat): i for i, p in enumerate(players)}
    if len(seat_to_index) != NUM_PLAYERS:
        raise ValueError("Each player must have a unique table seat ID")
    actor = seat_to_index[int(hero.seat)]
    card_info = np.zeros((4, 13, 6), dtype=np.float32)
    for card in hero.hand:
        parsed = _card(card)
        if parsed[0] is not None and parsed[1] is not None:
            card_info[parsed[0], parsed[1], 0] = 1
    for i, card in enumerate(board.public_cards):
        parsed = _card(card)
        if parsed[0] is not None and parsed[1] is not None:
            channel = 1 if i < 3 else (2 if i == 3 else 3)
            card_info[parsed[0], parsed[1], channel] = 1
            card_info[parsed[0], parsed[1], 4] = 1
            card_info[parsed[0], parsed[1], 5] = 1
    for card in hero.hand:
        parsed = _card(card)
        if parsed[0] is not None and parsed[1] is not None:
            card_info[parsed[0], parsed[1], 5] = 1

    legal = _legal_actions(getattr(board, "allowed", {}) or {}, hero)
    action_info = np.zeros((8, ACTION_COUNT, 81), dtype=np.float32)
    for street, records in enumerate(history or []):
        for index, (seat, action, legal_ids) in enumerate(records[-HISTORY_PER_STREET:]):
            slot = street * HISTORY_PER_STREET + index
            action_info[int(seat), int(action), slot] = 1
            action_info[6, int(action), slot] = 1
            for legal_id in legal_ids:
                action_info[7, int(legal_id), slot] = 1
    action_info[actor, :, -1] = 1
    table = np.zeros((NUM_PLAYERS, 5), dtype=np.float32)
    extras = np.zeros(NUM_PLAYERS, dtype=np.float32)
    for seat, p in enumerate(players):
        status = "folded" if p.is_fold else "allin" if float(p.stack or 0) <= 0 else "active"
        table[seat] = [contributions[seat] if contributions else p.bet,
                       status != "folded", status == "allin", p.is_dealer, p.is_me]
        extras[seat] = float(p.stack or 0)

    # Match actor_relative_observation(): rotate seat rows, leave aggregate and
    # legal-action rows fixed, and put the acting player at index zero.
    order = [(actor + i) % NUM_PLAYERS for i in range(NUM_PLAYERS)]
    table = table[order]
    extras = extras[order]
    action_info = np.concatenate((action_info[:NUM_PLAYERS][order], action_info[NUM_PLAYERS:]), axis=0)
    legal_mask = np.zeros(ACTION_COUNT, dtype=np.float32)
    legal_mask[legal] = 1
    call = max(float(hero.call_amount or 0), 0.0)
    stack = float(hero.stack or 0)
    effective = min(stack, max((float(p.stack or 0) for p in players if not p.is_me and not p.is_fold), default=0.0))
    street = 0 if len(board.public_cards) == 0 else len(board.public_cards) - 2
    has_raise = int(2 in legal or 3 in legal)
    has_all_in_opponent = int(any(not p.is_me and not p.is_fold and float(p.stack or 0) <= 0 for p in players))
    cost = min(call, stack)
    betting = np.asarray([[float(board.pot or 0), call, cost, float(last_raise_amount),
                           stack, effective, cost / max(float(board.pot or 0) + cost, 1.0),
                           effective / max(float(board.pot or 0), 1.0),
                           sum(1 for p in players if not p.is_me and not p.is_fold),
                           street, has_raise, has_all_in_opponent]], dtype=np.float32)
    return {"card_info": card_info[None], "action_info": action_info[None],
            "table_info": table[None], "extra_info": extras[None], "betting_info": betting,
            "legal_moves": legal_mask[None]}, legal


_MODEL = None


def _load_model(model_path=None):
    global _MODEL
    path = Path(model_path) if model_path else MODEL_PATH
    if _MODEL is not None and getattr(_MODEL, "_checkpoint_path", None) == path:
        return _MODEL
    if not path.is_file():
        raise FileNotFoundError(f"Six-player checkpoint not found: {path}")
    model = Policy()
    with path.open("rb") as stream:
        weights = pickle.load(stream)
    model.load_state_dict({key: torch.as_tensor(value) for key, value in weights.items()}, strict=True)
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    model.to(device).eval()
    model._checkpoint_path = path
    _MODEL = model
    return model


def choose_model_action(board, history=None, contributions=None, last_raise_amount=2.0, model_path=None):
    """Return an action string from the best policy using deterministic argmax."""
    observation, legal = _make_observation(
        board, history or [[], [], [], []], contributions, last_raise_amount)
    model = _load_model(model_path)
    device = next(model.parameters()).device
    tensors = {key: torch.as_tensor(value, device=device) for key, value in observation.items()}
    with torch.inference_mode():
        logits = model(tensors)[0].cpu().numpy()
    action_id = int(np.argmax(np.where(observation["legal_moves"][0] > 0, logits, -np.inf)))
    me = board.get_me()
    if action_id == 0:
        return "fold"
    if action_id == 1:
        return "check" if me.can_check else "call"
    if action_id == 4:
        amount = me.all_in
        if isinstance(amount, bool):
            amount = me.max_to or me.min_to
        return f"raise_{int(amount)}" if amount else ("call" if me.can_call else "check")
    pot = max(float(board.pot or 0), 0.0)
    call = max(float(me.call_amount or 0), 0.0)
    desired = call + int((pot + call) * (0.5 if action_id == 2 else 1.0))
    low = me.min_to if me.min_to is not None else desired
    high = me.max_to if me.max_to is not None else desired
    amount = min(int(high), max(int(low), int(desired)))
    return f"raise_{amount}"


def legacy_decision(board):
    """Original Monte Carlo decision policy, retained for A/B testing."""
    from src.strategy import sim_runs

    me = board.get_me()
    if not me:
        return "fold"

    winrate = sim_runs(board, 100)
    call_amount = me.call_amount or 0
    pot_size = board.pot

    if call_amount == 0:
        if winrate > 0.6 and me.min_to is not None:
            return f"raise_{me.min_to}"
        return "check"

    pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 1.0
    if winrate > pot_odds * 1.3:
        if me.min_to is not None and me.max_to is not None:
            raise_amount = min(me.max_to, max(me.min_to, int(pot_size * 0.5)))
            return f"raise_{raise_amount}"
        return "call"
    if winrate >= pot_odds:
        return "call"
    return "fold"


def decision(board, history=None, contributions=None, last_raise_amount=2.0):
    """Choose the configured model or original policy for A/B testing.

    Set POKER_AI_MODE=legacy to use the original Monte Carlo strategy;
    model is the default.
    """
    mode = os.environ.get("POKER_AI_MODE", "model").strip().lower()
    if mode in {"legacy", "original", "monte_carlo"}:
        return legacy_decision(board)
    if mode != "model":
        raise ValueError("POKER_AI_MODE must be 'model' or 'legacy'")
    try:
        return choose_model_action(board, history, contributions, last_raise_amount)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"Model decision unavailable; using legacy strategy: {exc}")
        return legacy_decision(board)
