# Shared-table Hold'em comparison

3,600 six-player hands, 600 independent deal blocks; six seat rotations per deal. Stacks reset to 100 BB each hand, no rake. All six strategies share every table. Monte Carlo uses 100 samples/decision and sees no opponents' cards.

| Strategy | Chips/hand | BB/100 | 95% CI (chips/hand) | Fold fraction |
|---|---:|---:|---|---:|
| trained | +18.03 | +901.6 | [+13.93, +22.13] | 38.4% |
| monte_carlo_aggressive | +11.41 | +570.5 | [+7.87, +14.94] | 47.9% |
| monte_carlo_original | +4.80 | +240.2 | [+2.71, +6.90] | 61.9% |
| monte_carlo_tight | +4.64 | +231.8 | [+2.86, +6.41] | 73.0% |
| random | -18.62 | -931.0 | [-23.26, -13.97] | 22.2% |
| check_call | -20.26 | -1013.1 | [-25.37, -15.16] | 0.0% |

Trained model minus each competitor (paired by deal block):

- monte_carlo_original: +13.23 chips/hand; 95% CI [8.49628815670885, 17.958711843291148].
- monte_carlo_tight: +13.40 chips/hand; 95% CI [8.939569725215549, 17.85209694145112].
- monte_carlo_aggressive: +6.62 chips/hand; 95% CI [0.9050656068485683, 12.339378837595877].
- check_call: +38.29 chips/hand; 95% CI [30.45992064432421, 46.127301577897995].
- random: +36.65 chips/hand; 95% CI [29.641261129861864, 43.660405536804795].

Assessment: The trained model's advantage over the original Monte Carlo policy is supported on this mixed table. The ranked average alone is insufficient when the paired interval overlaps zero. Results measure performance in this lineup, including exploitation of weak seats, rather than isolated heads-up strength. Continuous Monte Carlo raises retain their exact amounts; the model sees their nearest half-pot/pot history category. The tighter/aggressive variants use the same equity estimator with different betting rules. Intervals are approximate and are not adjusted for multiple comparisons.
