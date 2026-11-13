# Model health

No drift flags.

learn: train R4-R9, hold-out R10, R11
- new core: hold-out MAE R10 6.91, R11 6.18 vs current 6.91, 6.20 (gain +0.01)
→ kept current core
- shadow challenger 202611131616 ('new core', since R11) - would be promoted after 3 straight newest-round wins
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.24 → 0.25, RMSE +0.008
- kept tier layer (3 segment(s)): hold-out segment |bias| R10 1.47 → 1.57, R11 1.19 → 1.35, RMSE +0.039
- sd scale kept at 1.096 (hold-out 80% band 80%; candidate ×1.105 → 80%)

## Calibration (walk-forward)
- 80% band holds 80% of outcomes (above p90 13%, below p10 8%; n=1816) → sd scale that would make it 80%: ×1.009
## Error attribution
- minutes MAE 5.0 min · share of absolute error from minutes 34%, from rate 66%
- surprise DNPs (projected ≥10 min, played 0): 17 costing 99.7 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=279, err +0.05, ratio 0.995
- Guard|20-30: n=236, err -0.09, ratio 1.008
- Forward|15-20: n=220, err +0.11, ratio 0.987
- Forward|20-30: n=171, err +0.20, ratio 0.982
- Forward|10-15: n=165, err -0.12, ratio 1.02
- Guard|10-15: n=162, err +0.16, ratio 0.968
- Center|15-20: n=144, err -0.79, ratio 1.078
- Forward|<10: n=115, err -0.29, ratio 1.09
- Center|10-15: n=110, err -0.56, ratio 1.085
- Guard|<10: n=104, err -0.63, ratio 1.181
- Center|<10: n=78, err -1.40, ratio 1.419
- Center|20-30: n=32, err -3.11, ratio 1.224
## Bias by position x season-start price tier (after all corrections)
- Guard|9-13: n=310, err -0.40, ratio 1.045
- Guard|6-9: n=293, err +0.27, ratio 0.96
- Forward|6-9: n=250, err -0.13, ratio 1.018
- Forward|9-13: n=221, err -0.39, ratio 1.046
- Center|9-13: n=150, err -0.68, ratio 1.092
- Forward|<=6: n=137, err +0.92, ratio 0.804
- Center|6-9: n=137, err -1.04, ratio 1.148
- Guard|<=6: n=99, err +0.74, ratio 0.826
- Guard|13+: n=79, err -0.98, ratio 1.074
- Center|13+: n=63, err -2.21, ratio 1.175
- Forward|13+: n=63, err -0.03, ratio 1.003
- Center|<=6: n=14, err -0.08, ratio 1.026