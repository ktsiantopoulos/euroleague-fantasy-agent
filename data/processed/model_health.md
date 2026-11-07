# Model health

No drift flags.

learn: train R4-R8, hold-out R9, R10
- new core: hold-out MAE R9 6.02, R10 6.91 vs current 6.06, 6.91 (gain +0.02)
→ kept current core
- shadow challenger 202611051527 ('new core', since R10) - would be promoted after 3 straight newest-round wins
- kept bias layer (8 segment(s)): hold-out mean |bias| 0.37 → 0.37, RMSE +0.010
- sd scale kept at 1.096 (hold-out 80% band 80%; candidate ×1.12 → 80%)

## Calibration (walk-forward)
- 80% band holds 79% of outcomes (above p90 13%, below p10 8%; n=1592) → sd scale that would make it 80%: ×1.017
## Error attribution
- minutes MAE 4.94 min · share of absolute error from minutes 33%, from rate 67%
- surprise DNPs (projected ≥10 min, played 0): 15 costing 86.2 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=251, err -0.10, ratio 1.012
- Guard|20-30: n=196, err -0.06, ratio 1.005
- Forward|15-20: n=189, err +0.08, ratio 0.99
- Forward|10-15: n=152, err -0.02, ratio 1.004
- Forward|20-30: n=147, err +0.04, ratio 0.996
- Guard|10-15: n=145, err +0.33, ratio 0.933
- Center|15-20: n=127, err -0.66, ratio 1.065
- Center|10-15: n=101, err -0.35, ratio 1.055
- Forward|<10: n=100, err -0.55, ratio 1.175
- Guard|<10: n=92, err -0.89, ratio 1.26
- Center|<10: n=67, err -1.21, ratio 1.368
- Center|20-30: n=25, err -3.16, ratio 1.229