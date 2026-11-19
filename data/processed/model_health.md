# Model health

No drift flags.

learn: train R4-R10, hold-out R11, R12
- new core: hold-out MAE R11 6.18, R12 5.81 vs current 6.20, 5.81 (gain +0.01)
→ kept current core
- shadow challenger 202611131616 ('new core', since R11) - would be promoted after 3 straight newest-round wins
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.13 → 0.15, RMSE -0.002
- kept tier layer (3 segment(s)): hold-out segment |bias| R11 1.19 → 1.33, R12 1.40 → 1.22, RMSE -0.015
- sd scale kept at 1.096 (hold-out 80% band 82%; candidate ×1.115 → 83%)

## Calibration (walk-forward)
- 80% band holds 80% of outcomes (above p90 12%, below p10 8%; n=2043) → sd scale that would make it 80%: ×0.998
## Error attribution
- minutes MAE 5.05 min · share of absolute error from minutes 34%, from rate 66%
- surprise DNPs (projected ≥10 min, played 0): 21 costing 125.1 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=314, err -0.05, ratio 1.006
- Guard|20-30: n=273, err -0.10, ratio 1.008
- Forward|15-20: n=244, err +0.23, ratio 0.972
- Forward|20-30: n=196, err +0.45, ratio 0.96
- Forward|10-15: n=186, err -0.13, ratio 1.021
- Guard|10-15: n=178, err +0.17, ratio 0.965
- Center|15-20: n=156, err -0.93, ratio 1.091
- Forward|<10: n=129, err -0.46, ratio 1.143
- Center|10-15: n=124, err -0.63, ratio 1.096
- Guard|<10: n=117, err -0.38, ratio 1.11
- Center|<10: n=87, err -1.61, ratio 1.477
- Center|20-30: n=39, err -2.26, ratio 1.159
## Bias by position x season-start price tier (after all corrections)
- Guard|9-13: n=348, err -0.39, ratio 1.043
- Guard|6-9: n=332, err +0.32, ratio 0.954
- Forward|6-9: n=281, err -0.01, ratio 1.001
- Forward|9-13: n=249, err -0.28, ratio 1.033
- Center|9-13: n=165, err -0.69, ratio 1.095
- Forward|<=6: n=155, err +1.15, ratio 0.758
- Center|6-9: n=154, err -1.31, ratio 1.185
- Guard|<=6: n=113, err +0.81, ratio 0.811
- Guard|13+: n=89, err -1.34, ratio 1.101
- Center|13+: n=70, err -1.99, ratio 1.155
- Forward|13+: n=70, err -0.63, ratio 1.054
- Center|<=6: n=17, err +0.31, ratio 0.904