# Trade-discipline replay

Matchdays: 8, 9, 10, 11, 12, 13 · realised gain = recommended squad minus no-trade squad, both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +11.6 | +5.4 |
| current defaults | 10 | 4 | +26.9 | +45.4 |
| current defaults | 11 | 4 | +8.3 | +2.4 |
| current defaults | 12 | 4 | +13.8 | -8.8 |
| current defaults | 13 | 4 | +14.9 | +57.4 |
| no discipline | 8 | 4 | +18.1 | -2.2 |
| no discipline | 9 | 4 | +9.6 | -3.1 |
| no discipline | 10 | 4 | +26.9 | +45.4 |
| no discipline | 11 | 4 | +8.3 | +2.4 |
| no discipline | 12 | 4 | +13.8 | -8.8 |
| no discipline | 13 | 4 | +15.2 | +66.2 |

Predicted trade gain overshoots realised by 0.5 pts per trade (all grid settings).

Top grid settings by realised gain:

```
 trade_hurdle  trade_sd_penalty  min_games_in  trades  pred_gain  real_gain
          4.0               0.0             3      20       83.5      124.0
          4.0               0.0             1      20       81.6      116.6
          0.0               0.0             1      24       91.9       99.9
          2.0               0.0             1      24       91.9       99.9
          2.0               0.0             3      24       92.9       99.2
```