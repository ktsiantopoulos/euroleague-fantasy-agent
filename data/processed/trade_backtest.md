# Trade-discipline replay

Matchdays: 8, 9 · realised gain = recommended squad minus no-trade squad, both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +15.2 | +4.3 |
| no discipline | 8 | 4 | +14.7 | -9.8 |
| no discipline | 9 | 4 | +11.3 | -6.9 |

Predicted trade gain overshoots realised by 6.1 pts per trade (all grid settings).

Top grid settings by realised gain:

```
 trade_hurdle  trade_sd_penalty  min_games_in  trades  pred_gain  real_gain
          0.0              0.25             3       8       28.6       12.9
          0.0              0.50             1       7       27.9        1.9
          0.0              0.50             3       7       27.9        1.9
          2.0              0.25             3       7       27.9        1.9
          2.0              0.00             3       8       32.6        1.7
```