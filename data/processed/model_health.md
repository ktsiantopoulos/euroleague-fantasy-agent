# Model health

No drift flags.

learn: train R4-R7, hold-out R8, R9
- new core + bias: hold-out MAE R8 6.15, R9 5.68 vs current 6.11, 6.04 (gain +0.16)
- new core: hold-out MAE R8 6.09, R9 5.84 vs current 6.11, 6.04 (gain +0.10, every round)
- current core + new bias: hold-out MAE R8 6.19, R9 5.85 vs current 6.11, 6.04 (gain +0.05)
→ ADOPTED 'new core' (gain +0.10 on every hold-out round)
- sd scale kept at 1.096 (hold-out 80% band 79%; candidate ×1.122 → 79%)

## Calibration (walk-forward)
- 80% band holds 79% of outcomes (above p90 14%, below p10 7%; n=1206) → sd scale that would make it 80%: ×1.024
## Error attribution
- minutes MAE 4.95 min · share of absolute error from minutes 32%, from rate 68%
- surprise DNPs (projected ≥10 min, played 0): 8 costing 48.3 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|10-20: n=312, err -0.58, ratio 1.083
- Forward|10-20: n=270, err -0.81, ratio 1.122
- Center|10-20: n=179, err -0.86, ratio 1.107
- Guard|20-30: n=130, err -0.02, ratio 1.002
- Forward|20-30: n=99, err -0.62, ratio 1.056
- Forward|<10: n=80, err -1.22, ratio 1.503
- Guard|<10: n=73, err -1.85, ratio 1.866
- Center|<10: n=47, err -2.23, ratio 1.83
- Center|20-30: n=16, err -3.82, ratio 1.288