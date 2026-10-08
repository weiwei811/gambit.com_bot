from pathlib import Path
import sys

import numpy as np
import pytest

from tools.benchmark_shared_table import NAMES, public_board, step_ui_decision, summarize


def test_statistics_use_deal_blocks_and_paired_differences():
    rewards = np.zeros((4, 6, 6))
    rewards[:, :, 0] = np.arange(4)[:, None]
    rewards[:, :, 1] = -np.arange(4)[:, None]
    actions = np.zeros((6, 4, 5), dtype=int)
    result = summarize(rewards, actions, 4, 0)
    assert result["hands"] == 24
    assert result["strategies"][0]["chips_per_hand"] == 1.5
    assert result["paired_comparisons"][0]["chips_per_hand"] == 3.0
    assert result["confidence_unit"] == "six-rotation deal block"
    assert [row["strategy"] for row in result["strategies"]] == list(NAMES)


def test_public_cards_and_exact_continuous_raise_contract():
    alpha = Path(__file__).resolve().parents[2] / "alpha_holdem"
    if alpha.exists():
        sys.path.insert(0, str(alpha))
    module = pytest.importorskip("agi.nl_holdem_env")
    config = {"env_config": {"custom_options": {"num_players": 6, "betting_features": True}}}
    env = module.NlHoldemEnvWrapper(config)
    obs, _ = env.reset(seed=19)
    actor = env.my_agent()
    board = public_board(env)
    assert len(board.get_me().hand) == 2
    assert all(not p.hand for p in board.players if not p.is_me)
    before = env.env.game.players[actor].in_chips
    target = board.get_me().min_to + 1
    quantity = target - board.get_me().bet
    (obs, payoff, done, _, _), category = step_ui_decision(env, f"raise_{target}")
    assert env.env.game.players[actor].in_chips - before == quantity
    assert category in (2, 3)
    assert "_quantity" not in env.env.game.round.__dict__
    assert "get_nolimit_legal_actions" not in env.env.game.round.__dict__
    # One scripted fixture hand verifies settlement after the custom raise;
    # this is an engine contract test, not a model performance evaluation.
    for _ in range(100):
        if done:
            break
        assert obs["legal_moves"][1]
        obs, payoff, done, _, _ = env.step(1)
    assert done
    assert abs(sum(payoff)) < 1e-6
