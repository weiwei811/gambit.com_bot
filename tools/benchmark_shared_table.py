"""Shared-table tournament; run performance evaluation on Modal only."""
import json
import math
from pathlib import Path
import random
import sys
import time

import numpy as np

NAMES = ("trained", "monte_carlo_original", "monte_carlo_tight",
         "monte_carlo_aggressive", "check_call", "random")


def public_board(env):
    """Expose only actor cards, public cards, and public chip state."""
    from src.dataclass import Board, Player
    from rlcard.games.limitholdem import PlayerStatus
    game = env.env.game
    actor = env.my_agent()
    def card(c):
        rank = "23456789TJQKA".index(c.rank) + 2
        return (1 if rank == 14 else rank, c.suit.lower())
    call = max(game.round.raised) - game.round.raised[actor]
    board = Board(pot=sum(p.in_chips for p in game.players),
                  public_cards=[card(c) for c in game.public_cards])
    raises = 4 in env.last_obs[0]["legal_actions"]
    for i, p in enumerate(game.players):
        player = Player(seat=i, stack=p.remained_chips, bet=game.round.raised[i],
                        is_me=i == actor, is_dealer=i == game.dealer_id,
                        is_fold=p.status == PlayerStatus.FOLDED,
                        hand=[card(c) for c in p.hand] if i == actor else [])
        if i == actor:
            player.call_amount = min(call, p.remained_chips)
            player.can_check = call == 0
            player.can_call = True
            if raises:
                player.max_to = game.round.raised[i] + p.remained_chips
                player.min_to = min(player.max_to, max(game.round.raised) + game.round.last_raise_amount)
        board.players.append(player)
    return board


def monte_carlo_decision(name, board):
    if name == "monte_carlo_original":
        from src.ai_decision import legacy_decision
        return legacy_decision(board)
    from src.strategy import sim_runs
    equity = sim_runs(board, 100)
    me = board.get_me()
    call = me.call_amount or 0
    odds = call / max(board.pot + call, 1)
    if name == "monte_carlo_tight":
        if equity > 0.65 and me.min_to is not None:
            return f"raise_{me.min_to}"
        return "check" if call == 0 else "call" if equity >= 1.25 * odds else "fold"
    if me.min_to is not None and (equity > max(0.25, 1.1 * odds) or (call == 0 and random.random() < 0.2)):
        target = min(me.max_to, max(me.min_to, me.bet + call + board.pot + call))
        return f"raise_{target}"
    return "check" if call == 0 else "call" if equity >= 0.85 * odds else "fold"


def step_ui_decision(env, choice):
    """Execute continuous raise-to amounts without changing engine files.

    Historical model action categories use the nearest half-pot/pot class.
    The actual amount charged to the player remains the strategy's amount.
    """
    from rlcard.games.nolimitholdem import Action
    game = env.env.game
    legal = env.last_obs[0]["legal_actions"]
    if choice in ("check", "call"):
        return env.step(1), 1
    if choice == "fold":
        return env.step(0), 0
    if not choice.startswith("raise_") or 4 not in legal:
        raise ValueError("Illegal UI strategy decision: " + choice)
    actor = env.my_agent()
    round_ = game.round
    quantity = int(choice.split("_", 1)[1]) - round_.raised[actor]
    if quantity >= game.players[actor].remained_chips:
        return env.step(4), 4
    call = max(round_.raised) - round_.raised[actor]
    if quantity - call < round_.last_raise_amount or quantity <= call:
        raise ValueError("Continuous raise violates minimum raise")
    original_quantity = round_._quantity
    original_legal = round_.get_nolimit_legal_actions
    stage = game.stage
    half = original_quantity(Action.RAISE_HALF_POT, game.players)
    pot = original_quantity(Action.RAISE_POT, game.players)
    category = 2 if abs(quantity - half) <= abs(quantity - pot) else 3
    marker = Action(category)
    def applies():
        return game.game_pointer == actor and game.stage == stage
    def custom_quantity(action, players):
        return quantity if applies() and action == marker else original_quantity(action, players)
    def custom_legal(players):
        actions = original_legal(players)
        if applies() and Action.ALL_IN in actions and marker not in actions:
            actions.append(marker)
        return actions
    round_._quantity = custom_quantity
    round_.get_nolimit_legal_actions = custom_legal
    # The wrapper logs its pre-action legal mask; make the valid continuous
    # action available there even when the default fixed sizing was illegal.
    env.last_obs[0]["legal_actions"][category] = None
    if marker not in env.last_obs[0]["raw_obs"]["legal_actions"]:
        env.last_obs[0]["raw_obs"]["legal_actions"].append(marker)
    try:
        return env.step(category), category
    finally:
        del round_._quantity
        del round_.get_nolimit_legal_actions


def summarize(rewards, actions, target_blocks, elapsed):
    # All six rotations within a deal form one correlated statistical block.
    blocks = rewards.mean(axis=1)
    def interval(values):
        mean = float(values.mean())
        radius = 1.96 * float(values.std(ddof=1)) / math.sqrt(len(values)) if len(values) > 1 else None
        return [mean - radius, mean + radius] if radius is not None else None
    rows = []
    for i, name in enumerate(NAMES):
        ci = interval(blocks[:, i])
        counts = actions[i].sum(axis=0)
        rows.append({"strategy": name, "chips_per_hand": float(blocks[:, i].mean()),
                     "bb_per_100": float(blocks[:, i].mean() * 50),
                     "95pct_ci_chips": ci, "positive_payoff_fraction": float((rewards[:, :, i] > 0).mean()),
                     "action_counts": counts.tolist(), "street_action_counts": actions[i].tolist()})
    comparisons = []
    for i in range(1, len(NAMES)):
        delta = blocks[:, 0] - blocks[:, i]
        comparisons.append({"trained_minus": NAMES[i], "chips_per_hand": float(delta.mean()),
                            "95pct_ci_chips": interval(delta)})
    return {"strategies": rows, "paired_comparisons": comparisons,
            "completed_deal_blocks": len(rewards), "requested_deal_blocks": target_blocks,
            "hands": len(rewards) * 6, "complete": len(rewards) == target_blocks,
            "elapsed_seconds": elapsed, "big_blind": 2, "starting_stack": 200,
            "rake": 0, "monte_carlo_samples_per_decision": 100,
            "model_action_selection": "deterministic", "confidence_unit": "six-rotation deal block"}


def write_report(out, summary):
    rows = sorted(summary["strategies"], key=lambda row: -row["chips_per_hand"])
    report = "# Shared-table Hold'em comparison\n\n"
    report += f"{summary['hands']:,} six-player hands, {summary['completed_deal_blocks']} independent deal blocks; six seat rotations per deal. Stacks reset to 100 BB each hand, no rake. All six strategies share every table. Monte Carlo uses 100 samples/decision and sees no opponents' cards.\n\n"
    report += "| Strategy | Chips/hand | BB/100 | 95% CI (chips/hand) | Fold fraction |\n|---|---:|---:|---|---:|\n"
    for row in rows:
        ci = row["95pct_ci_chips"]
        counts = row["action_counts"]
        ci_text = f"[{ci[0]:+.2f}, {ci[1]:+.2f}]" if ci else "insufficient blocks"
        report += f"| {row['strategy']} | {row['chips_per_hand']:+.2f} | {row['bb_per_100']:+.1f} | {ci_text} | {counts[0]/max(sum(counts),1):.1%} |\n"
    report += "\nTrained model minus each competitor (paired by deal block):\n\n"
    for row in summary["paired_comparisons"]:
        report += f"- {row['trained_minus']}: {row['chips_per_hand']:+.2f} chips/hand; 95% CI {row['95pct_ci_chips']}.\n"
    original = summary["paired_comparisons"][0]
    ci = original["95pct_ci_chips"]
    if ci and ci[0] > 0:
        verdict = "The trained model's advantage over the original Monte Carlo policy is supported on this mixed table."
    elif ci and ci[1] < 0:
        verdict = "The original Monte Carlo policy has a supported advantage over the trained model on this mixed table."
    else:
        verdict = "The comparison does not establish a reliable advantage between the trained model and the original Monte Carlo policy."
    report += "\nAssessment: " + verdict + " The ranked average alone is insufficient when the paired interval overlaps zero. Results measure performance in this lineup, including exploitation of weak seats, rather than isolated heads-up strength. Continuous Monte Carlo raises retain their exact amounts; the model sees their nearest half-pot/pot history category. The tighter/aggressive variants use the same equity estimator with different betting rules. Intervals are approximate and are not adjusted for multiple comparisons.\n"
    if not summary["complete"]:
        report += "\nThe time ceiling stopped this evaluation early; only fully completed rotation blocks are included.\n"
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    (out / "report.md").write_text(report, encoding="utf-8")


def initialize_worker(config_path, model_path):
    global _ENV, _AGENT
    import torch
    from agi.nl_holdem_env import NlHoldemEnvWrapper
    from agi.evaluation_tools import NNAgent
    torch.set_num_threads(1)
    config = json.loads(Path(config_path).read_text())
    _ENV = NlHoldemEnvWrapper(config)
    _AGENT = NNAgent(_ENV.observation_space, _ENV.action_space, config, model_path, device="cpu")


def evaluate_block(task):
    block, seed, deadline = task
    env, agent = _ENV, _AGENT
    block_rewards = []
    block_actions = np.zeros((6, 4, 5), dtype=np.int64)
    for rotation in range(6):
        obs, _ = env.reset(seed=seed + block)
        done = False
        counts = [0] * 6
        while not done:
            if deadline and time.time() >= deadline:
                return None
            seat = env.my_agent()
            index = (seat - rotation) % 6
            name = NAMES[index]
            decision_seed = seed + block * 100000 + rotation * 10000 + index * 1000 + counts[index]
            random.seed(decision_seed)
            counts[index] += 1
            street = env.last_obs[0]["raw_obs"]["stage"].value
            if name == "trained":
                action = agent.make_action(obs, deterministic=True)
                result = env.step(action)
            elif name == "check_call":
                action = 1
                result = env.step(action)
            elif name == "random":
                action = random.choice(list(env.last_obs[0]["legal_actions"]))
                result = env.step(action)
            else:
                choice = monte_carlo_decision(name, public_board(env))
                result, action = step_ui_decision(env, choice)
            block_actions[index, street, action] += 1
            obs, payoff, done, _, _ = result
        if abs(sum(payoff)) > 1e-6:
            raise ValueError("Non-zero-sum payoff")
        block_rewards.append([float(payoff[(i + rotation) % 6]) for i in range(6)])
    return np.asarray(block_rewards), block_actions


def run_benchmark(config_path, model_path, output, target_blocks=600, seed=68000000,
                  deadline=None, commit=None):
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    history_path = out / "completed_blocks.npz"
    actions = np.zeros((6, 4, 5), dtype=np.int64)
    rewards = []
    if history_path.exists():
        with np.load(history_path) as data:
            rewards = list(data["rewards"])
            actions = data["actions"].copy()
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=4, mp_context=multiprocessing.get_context("spawn"),
                             initializer=initialize_worker,
                             initargs=(str(config_path), str(model_path))) as pool:
        for start in range(len(rewards), target_blocks, 10):
            tasks = [(block, seed, deadline) for block in range(start, min(start+10, target_blocks))]
            timed_out = False
            for result in pool.map(evaluate_block, tasks):
                if result is None:
                    timed_out = True
                    break
                block_rewards, block_actions = result
                rewards.append(block_rewards)
                actions += block_actions
            if rewards:
                np.savez_compressed(history_path, rewards=np.asarray(rewards), actions=actions)
                print(json.dumps({"completed_blocks": len(rewards), "hands": len(rewards)*6,
                                  "elapsed_seconds": round(time.monotonic()-started, 1)}), flush=True)
                if commit:
                    commit()
            if timed_out:
                print("Time ceiling reached; retaining complete blocks only.", flush=True)
                break
    if not rewards:
        raise RuntimeError("No complete deal blocks; inspect evaluation.log")
    np.savez_compressed(history_path, rewards=np.asarray(rewards), actions=actions)
    summary = summarize(np.asarray(rewards), actions, target_blocks, time.monotonic()-started)
    write_report(out, summary)
    print((out / "report.md").read_text(), flush=True)
    return summary
