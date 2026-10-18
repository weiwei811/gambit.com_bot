# Gambit Hold’em bot

This bot connects to a logged-in Chrome session and uses the six-player Alpha Hold’em policy from `models/six_player_best_2026-10-06.pkl` to choose actions. The model is loaded locally; inference uses CUDA when available, Apple MPS on supported Macs, and CPU otherwise.

## Setup

Use Python 3.11, then install the dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS, activate with `source .venv/bin/activate`. The requirement markers select a PyTorch build for Apple Silicon or Intel Macs. On Windows, install the matching CUDA-enabled PyTorch wheel from the official PyTorch instructions if GPU inference is desired; the default PyPI wheel may use CPU only.

## Run

1. Start Chrome with remote debugging on port `9222` and sign in to Gambit.
2. Run `python main.py`.
3. Stop the bot with Ctrl+C.

The main loop keeps a per-hand record of public actions from successive game snapshots. `src/ai_decision.py` converts the six seats, cards, stacks, pot, legal actions, and action history into the model’s training observation, applies the legal-action mask, and takes the highest-scoring legal action. Raise actions are mapped to the closest supported half-pot or pot sizing and clamped to the UI’s allowed range.

For A/B testing, set `POKER_AI_MODE=legacy` before starting `main.py` to use the original Monte Carlo decision implementation. The default is `POKER_AI_MODE=model`; restart the bot after changing the setting.

`tools/benchmark_shared_table.py` defines an offline six-strategy comparison using the Alpha Hold'em engine: the trained model, original Monte Carlo strategy, tight/aggressive Monte Carlo variants, check/call, and random play. It replays each deal with all six seat rotations, keeps opponents' cards hidden, and reports profit and paired uncertainty by deal. The bounded Modal runner is `tools/modal_shared_table_benchmark.py` in the sibling Alpha Hold'em repository; performance runs execute on Modal and write `report.md`, `summary.json`, `evaluation.log`, and raw deal-block results.

The [2026-10-08 shared-table report](results/shared_table_2026-10-08/report.md) covers 3,600 hands. The trained model earned +18.03 chips/hand versus +4.80 for the original Monte Carlo strategy; the paired advantage was +13.23 with approximate 95% interval [+8.50, +17.96]. This result applies to that mixed lineup, which also contains random and check/call opponents.

## Model details and limits

The bundled checkpoint is the verified six-player structured model dated 2026-10-06. It was benchmarked at +18.14 chips per hand against the project’s fixed benchmark pool; that benchmark does not establish optimal play. The policy supports six seats and requires the hero’s two visible cards. If model inference cannot run, the bot falls back to the existing Monte Carlo strategy.

The browser data source is an undocumented client store and may change. The action history is reconstructed from observed snapshots, so transitions missed while the bot is not polling cannot be recovered. Review the printed action and the UI before using it with real stakes.

Table seat IDs (including one-based or sparse IDs) are mapped to six dense model rows in numeric seat order. Snapshot list reordering does not change player identity. Unsupported table sizes use the legacy policy.
