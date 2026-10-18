from src.ai_decision import GameHistory, _load_model, _make_observation, choose_model_action, decision
from src.dataclass import Board, Player, data2board
import copy
import numpy as np
import pytest


def _snapshot(hand_id="hand-1", actor=0, folded=None, bet=2, street="preflop"):
    players = []
    for seat in range(6):
        players.append({
            "seat": seat,
            "name": f"p{seat}",
            "stack": 198 if seat == actor else 200,
            "bet": bet if seat == actor else 0,
            "cards": ["As", "Kd"] if seat == 0 else None,
            "isTurn": seat == actor,
            "isDealer": seat == 5,
            "status": "folded" if seat == folded else "active",
        })
    return {
        "ready": True,
        "handId": hand_id,
        "heroSeat": 0,
        "players": players,
        "board": [],
        "street": street,
        "pot": 3,
        "allowed": {"fold": True, "check": True, "call": 0,
                    "allIn": 198, "betRaise": {"minTo": 4, "maxTo": 198}},
    }


def test_best_checkpoint_loads_strictly():
    model = _load_model()
    assert len(model.state_dict()) == 92


def test_snapshot_history_records_fold_once_and_resets_by_hand():
    tracker = GameHistory()
    tracker.observe(_snapshot(actor=2, folded=None))
    after_fold = _snapshot(actor=3, folded=2)
    tracker.observe(after_fold)
    assert tracker.history[0] == [(2, 0, [0, 1, 2, 3, 4])]
    tracker.observe(after_fold)
    assert len(tracker.history[0]) == 1
    tracker.observe(_snapshot(hand_id="hand-2", actor=1))
    assert tracker.history == [[], [], [], []]


def test_model_observation_has_six_seat_contract():
    board = data2board(_snapshot())
    observation, legal = _make_observation(board, [[], [], [], []], [2, 0, 0, 0, 0, 0])
    assert legal == [0, 1, 2, 3, 4]
    assert observation["card_info"].shape == (1, 4, 13, 6)
    assert observation["action_info"].shape == (1, 8, 5, 81)
    assert observation["table_info"].shape == (1, 6, 5)
    assert observation["betting_info"].shape == (1, 12)


def test_call_is_not_misclassified_as_a_raise():
    tracker = GameHistory()
    before = _snapshot(actor=2, bet=10)
    before["pot"] = 30
    before["allowed"]["call"] = 2
    tracker.observe(before)
    after = _snapshot(actor=3, bet=0)
    after["pot"] = 32
    after["players"][2]["bet"] = 12
    tracker.observe(after)
    assert tracker.history[0][0][1] == 1
    assert tracker.contributions[2] == 12


def test_inference_selects_only_legal_check_or_fold():
    data = _snapshot()
    data["allowed"] = {"fold": True, "check": True, "call": 0}
    board = data2board(data)
    action = choose_model_action(board, [[], [], [], []], [0] * 6)
    assert action in {"fold", "check"}


def test_legacy_switch_preserves_original_decision(monkeypatch):
    monkeypatch.setenv("POKER_AI_MODE", "legacy")
    monkeypatch.setattr("src.strategy.sim_runs", lambda board, n: 0.9)
    board = Board(players=[Player(is_me=True, call_amount=0, min_to=4, max_to=50)], pot=10)
    assert decision(board) == "raise_4"


def _relabel(data, seats):
    data = copy.deepcopy(data)
    data["heroSeat"] = seats[data["heroSeat"]]
    for player in data["players"]:
        player["seat"] = seats[player["seat"]]
    return data


@pytest.mark.parametrize("seats", [(1, 2, 3, 4, 5, 6), (2, 4, 7, 9, 12, 20)])
def test_table_ids_map_to_dense_history_and_model_rows(seats):
    before = _snapshot(actor=5, bet=0)
    after = _snapshot(actor=0, bet=0)
    after["players"][5]["bet"] = 10
    after["pot"] = 13
    reference = GameHistory()
    reference.observe(before)
    reference.observe(after)
    tracker = GameHistory()
    tracker.observe(_relabel(before, seats))
    tracker.observe(_relabel(after, seats))
    assert tracker.history == reference.history
    assert tracker.contributions == reference.contributions
    expected, _ = _make_observation(data2board(after), reference.history, reference.contributions)
    actual, _ = _make_observation(data2board(_relabel(after, seats)), tracker.history, tracker.contributions)
    for key in expected:
        np.testing.assert_array_equal(actual[key], expected[key])


def test_history_matches_players_by_seat_when_snapshot_order_changes():
    before = _snapshot(actor=5, bet=0)
    after = _snapshot(actor=0, folded=5, bet=0)
    after["players"].reverse()
    tracker = GameHistory()
    tracker.observe(before)
    tracker.observe(after)
    assert tracker.history[0][0][0:2] == (5, 0)


def test_hero_in_highest_string_seat_uses_dense_actor_row():
    data = _snapshot(actor=5)
    data["heroSeat"] = "6"
    for player in data["players"]:
        player["seat"] = str(player["seat"] + 1)
        player["cards"] = ["As", "Kd"] if player["seat"] == "6" else None
    tracker = GameHistory()
    tracker.observe(data)
    board = data2board(data)
    assert board.get_me().seat == 6
    observation, _ = _make_observation(board, tracker.history, tracker.contributions)
    assert observation["table_info"][0, 0, 4] == 1
    assert observation["action_info"][0, 0, :, -1].sum() == 5
    assert observation["extra_info"][0, 0] == 198


def test_unsupported_table_does_not_crash_history_tracker():
    data = _snapshot()
    data["players"].append({"seat": 8, "bet": 2, "isTurn": True})
    tracker = GameHistory()
    tracker.observe(data)
    tracker.observe(data)
    assert tracker.previous is None
    assert tracker.history == [[], [], [], []]
