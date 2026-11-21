# Model health

**DRIFT:** model lost to a naive baseline in R12 and R13

learn: train R4-R11, hold-out R12, R13
- new core: hold-out MAE R12 5.81, R13 6.65 vs current 5.81, 6.69 (gain +0.02)
→ kept current core
- shadow challenger 202611131616 ('new core', since R11) - would be promoted after 3 straight newest-round wins
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.11 → 0.11, RMSE -0.026
- kept tier layer (3 segment(s)): hold-out segment |bias| R12 1.40 → 1.30, R13 1.04 → 1.08, RMSE -0.011
- sd scale kept at 1.096 (hold-out 80% band 82%; candidate ×1.106 → 82%)

## Calibration (walk-forward)
- 80% band holds 80% of outcomes (above p90 12%, below p10 7%; n=2272) → sd scale that would make it 80%: ×0.993
## Error attribution
- minutes MAE 5.04 min · share of absolute error from minutes 34%, from rate 66%
- surprise DNPs (projected ≥10 min, played 0): 23 costing 131.3 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=342, err +0.03, ratio 0.996
- Guard|20-30: n=314, err -0.31, ratio 1.028
- Forward|15-20: n=267, err +0.37, ratio 0.954
- Forward|20-30: n=223, err +0.59, ratio 0.947
- Forward|10-15: n=208, err -0.27, ratio 1.043
- Guard|10-15: n=198, err +0.22, ratio 0.955
- Center|15-20: n=168, err -0.81, ratio 1.078
- Forward|<10: n=140, err -0.31, ratio 1.097
- Center|10-15: n=139, err -0.91, ratio 1.141
- Guard|<10: n=129, err -0.42, ratio 1.12
- Center|<10: n=93, err -1.34, ratio 1.402
- Center|20-30: n=50, err -1.52, ratio 1.109
## Bias by position x season-start price tier (after all corrections)
- Guard|9-13: n=387, err -0.53, ratio 1.059
- Guard|6-9: n=368, err +0.31, ratio 0.956
- Forward|6-9: n=311, err +0.04, ratio 0.995
- Forward|9-13: n=278, err -0.14, ratio 1.016
- Center|9-13: n=179, err -0.77, ratio 1.105
- Center|6-9: n=172, err -1.19, ratio 1.164
- Forward|<=6: n=168, err +1.19, ratio 0.754
- Guard|<=6: n=129, err +0.75, ratio 0.826
- Guard|13+: n=99, err -1.02, ratio 1.076
- Center|13+: n=77, err -1.53, ratio 1.117
- Forward|13+: n=77, err -0.51, ratio 1.043
- Center|<=6: n=22, err -0.11, ratio 1.03