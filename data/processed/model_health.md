# Model health

No drift flags.

learn: train R4-R12, hold-out R13, R14
- new core: hold-out MAE R13 6.65, R14 6.22 vs current 6.69, 6.29 (gain +0.06, every round)
→ ADOPTED 'new core' (gain +0.06 on every hold-out round)
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.18 → 0.17, RMSE +0.006
- kept tier layer (3 segment(s)): hold-out segment |bias| R13 1.12 → 1.24, R14 0.66 → 0.57, RMSE +0.027
- sd scale kept at 1.096 (hold-out 80% band 83%; candidate ×1.088 → 83%)

## Calibration (walk-forward)
- 80% band holds 81% of outcomes (above p90 12%, below p10 7%; n=2497) → sd scale that would make it 80%: ×0.977
## Error attribution
- minutes MAE 5.04 min · share of absolute error from minutes 34%, from rate 66%
- surprise DNPs (projected ≥10 min, played 0): 26 costing 164.6 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=370, err -0.04, ratio 1.005
- Guard|20-30: n=354, err -0.35, ratio 1.031
- Forward|15-20: n=290, err +0.26, ratio 0.968
- Forward|20-30: n=249, err +0.54, ratio 0.951
- Forward|10-15: n=229, err +0.03, ratio 0.995
- Guard|10-15: n=214, err +0.59, ratio 0.886
- Center|15-20: n=180, err -1.13, ratio 1.113
- Center|10-15: n=153, err -0.92, ratio 1.144
- Forward|<10: n=152, err -0.13, ratio 1.04
- Guard|<10: n=145, err +0.03, ratio 0.993
- Center|<10: n=100, err -1.23, ratio 1.369
- Center|20-30: n=60, err -1.26, ratio 1.095
## Bias by position x season-start price tier (after all corrections)
- Guard|9-13: n=423, err -0.53, ratio 1.057
- Guard|6-9: n=405, err +0.45, ratio 0.937
- Forward|6-9: n=340, err +0.22, ratio 0.971
- Forward|9-13: n=304, err -0.24, ratio 1.028
- Center|9-13: n=193, err -0.71, ratio 1.098
- Forward|<=6: n=184, err +1.37, ratio 0.729
- Center|6-9: n=179, err -1.22, ratio 1.173
- Guard|<=6: n=146, err +1.20, ratio 0.745
- Guard|13+: n=109, err -1.34, ratio 1.105
- Center|13+: n=85, err -2.11, ratio 1.172
- Forward|13+: n=85, err -0.82, ratio 1.07
- Center|<=6: n=25, err +0.42, ratio 0.901