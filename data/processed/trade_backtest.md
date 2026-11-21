# Trade-discipline replay

Matchdays: 8, 9, 10, 11, 12, 13 · realised gain = recommended squad minus no-trade squad, both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +15.2 | +4.3 |
| current defaults | 10 | 4 | +25.3 | +34.1 |
| current defaults | 11 | 4 | +8.3 | +2.4 |
| current defaults | 12 | 4 | +12.5 | -10.2 |
| current defaults | 13 | 4 | +14.9 | +57.4 |
| no discipline | 8 | 4 | +14.7 | -9.8 |
| no discipline | 9 | 4 | +11.3 | -6.9 |
| no discipline | 10 | 4 | +25.3 | +34.1 |
| no discipline | 11 | 4 | +8.3 | +2.4 |
| no discipline | 12 | 4 | +12.5 | -10.2 |
| no discipline | 13 | 4 | +15.2 | +66.2 |

Predicted trade gain overshoots realised by 0.8 pts per trade (all grid settings).

Top grid settings by realised gain:

```
 trade_hurdle  trade_sd_penalty  min_games_in  trades  pred_gain  real_gain
          2.0              0.25             3      20       82.2       97.8
          4.0              0.00             1      21       79.3       97.7
          4.0              0.00             3      20       84.4       91.8
          0.0              0.25             3      24       90.9       86.9
          2.0              0.00             3      24       93.6       85.4
```