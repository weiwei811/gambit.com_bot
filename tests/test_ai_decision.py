from src.ai_decision import GameHistory, _load_model, _make_observation, choose_model_action, decision
from src.dataclass import Board, Player, data2board


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
