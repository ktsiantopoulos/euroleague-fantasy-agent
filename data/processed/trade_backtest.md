# Trade-discipline replay

Matchdays: 8, 9, 10, 11 · realised gain = recommended squad minus no-trade squad, both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +15.2 | +4.3 |
| current defaults | 10 | 4 | +25.3 | +34.1 |
| current defaults | 11 | 4 | +8.3 | +2.4 |
| no discipline | 8 | 4 | +14.7 | -9.8 |
| no discipline | 9 | 4 | +11.3 | -6.9 |
| no discipline | 10 | 4 | +25.3 | +34.1 |
| no discipline | 11 | 4 | +8.3 | +2.4 |

Predicted trade gain overshoots realised by 2.8 pts per trade (all grid settings).

Top grid settings by realised gain:

```
 trade_hurdle  trade_sd_penalty  min_games_in  trades  pred_gain  real_gain
          0.0              0.50             1      15       62.1       43.0
          0.0              0.50             3      15       62.1       43.0
          0.0              0.25             3      16       63.5       39.7
          0.0              0.00             3      16       66.2       38.2
          3.0              0.00             3      16       66.2       38.2
```