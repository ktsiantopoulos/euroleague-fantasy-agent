# Trade-discipline replay

Matchdays: 8, 9, 10 · realised gain = recommended squad minus no-trade squad, both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +15.2 | +4.3 |
| current defaults | 10 | 4 | +25.3 | +34.1 |
| no discipline | 8 | 4 | +14.7 | -9.8 |
| no discipline | 9 | 4 | +11.3 | -6.9 |
| no discipline | 10 | 4 | +25.3 | +34.1 |

Predicted trade gain overshoots realised by 2.8 pts per trade (all grid settings).

Top grid settings by realised gain:

```
 trade_hurdle  trade_sd_penalty  min_games_in  trades  pred_gain  real_gain
          0.0              0.25             3      12       53.9       47.0
          0.0              0.50             1      11       53.2       36.0
          0.0              0.50             3      11       53.2       36.0
          2.0              0.25             3      11       53.2       36.0
          2.0              0.00             3      12       57.9       35.8
```