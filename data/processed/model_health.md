# Model health

No drift flags.

learn: train R4-R6, hold-out R7, R8
- new core + bias: hold-out MAE R7 6.45, R8 6.13 vs current 6.46, 6.11 (gain -0.01)
- new core: hold-out MAE R7 6.45, R8 6.09 vs current 6.46, 6.11 (gain +0.01, every round)
- current core + new bias: hold-out MAE R7 6.40, R8 6.16 vs current 6.46, 6.11 (gain +0.00)
→ kept current core
- shadow challenger 202610290458 ('new core', since R8) - would be promoted after 3 straight newest-round wins
→ sd scale 1.0 → 1.096 (hold-out 80% band 73% → 77%)

## Calibration (walk-forward)
- 80% band holds 79% of outcomes (above p90 14%, below p10 7%; n=1134) → sd scale that would make it 80%: ×1.029
## Error attribution
- minutes MAE 5.01 min · share of absolute error from minutes 32%, from rate 68%
- surprise DNPs (projected ≥10 min, played 0): 8 costing 42.6 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|10-20: n=291, err -0.67, ratio 1.097
- Forward|10-20: n=252, err -0.68, ratio 1.102
- Center|10-20: n=164, err -0.94, ratio 1.115
- Guard|20-30: n=126, err +0.34, ratio 0.971
- Forward|20-30: n=90, err -0.57, ratio 1.051
- Forward|<10: n=80, err -1.40, ratio 1.588
- Guard|<10: n=68, err -2.18, ratio 2.027
- Center|<10: n=46, err -2.61, ratio 1.985
- Center|20-30: n=17, err -3.46, ratio 1.265