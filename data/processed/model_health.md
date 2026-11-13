# Model health

**DRIFT:** model lost to a naive baseline in R10 and R11

learn: train R4-R9, hold-out R10, R11
- new core: hold-out MAE R10 6.91, R11 6.24 vs current 6.91, 6.21 (gain -0.02)
→ kept current core
- shadow challenger 202611131616 ('new core', since R11) - would be promoted after 3 straight newest-round wins
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.24 → 0.25, RMSE +0.008
- kept tier layer (3 segment(s)): hold-out segment |bias| R10 1.47 → 1.57, R11 1.18 → 1.58, RMSE +0.052
- sd scale kept at 1.096 (hold-out 80% band 80%; candidate ×1.105 → 80%)

## Calibration (walk-forward)
- 80% band holds 80% of outcomes (above p90 13%, below p10 8%; n=1749) → sd scale that would make it 80%: ×1.008
## Error attribution
- minutes MAE 4.99 min · share of absolute error from minutes 34%, from rate 66%
- surprise DNPs (projected ≥10 min, played 0): 16 costing 93.4 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=272, err -0.03, ratio 1.004
- Guard|20-30: n=225, err +0.02, ratio 0.998
- Forward|15-20: n=212, err +0.13, ratio 0.984
- Forward|20-30: n=163, err +0.21, ratio 0.981
- Forward|10-15: n=160, err -0.13, ratio 1.021
- Guard|10-15: n=156, err +0.19, ratio 0.962
- Center|15-20: n=138, err -0.72, ratio 1.07
- Center|10-15: n=109, err -0.51, ratio 1.076
- Forward|<10: n=109, err -0.33, ratio 1.105
- Guard|<10: n=101, err -0.81, ratio 1.234
- Center|<10: n=74, err -1.27, ratio 1.382
- Center|20-30: n=30, err -3.89, ratio 1.284
## Bias by position x season-start price tier (after all corrections)
- Guard|9-13: n=294, err -0.28, ratio 1.031
- Guard|6-9: n=285, err +0.11, ratio 0.983
- Forward|6-9: n=237, err -0.05, ratio 1.006
- Forward|9-13: n=214, err -0.44, ratio 1.051
- Center|9-13: n=144, err -0.54, ratio 1.074
- Forward|<=6: n=133, err +0.83, ratio 0.822
- Center|6-9: n=131, err -1.02, ratio 1.145
- Guard|<=6: n=98, err +0.69, ratio 0.839
- Guard|13+: n=77, err -0.96, ratio 1.073
- Center|13+: n=62, err -2.46, ratio 1.197
- Forward|13+: n=60, err +0.01, ratio 0.999
- Center|<=6: n=14, err -0.08, ratio 1.026