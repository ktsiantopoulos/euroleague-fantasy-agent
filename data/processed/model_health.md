# Model health

No drift flags.

learn: train R4-R8, hold-out R9, R10
- new core: hold-out MAE R9 6.02, R10 8.51 vs current 6.06, 8.29 (gain -0.09)
→ kept current core
- shadow challenger 202611051527 ('new core', since R10) - would be promoted after 3 straight newest-round wins
- kept bias layer (8 segment(s)): hold-out mean |bias| 1.70 → 1.71, RMSE -0.003
- sd scale kept at 1.096 (hold-out 80% band 81%; candidate ×1.12 → 82%)

## Calibration (walk-forward)
- 80% band holds 80% of outcomes (above p90 13%, below p10 8%; n=1387) → sd scale that would make it 80%: ×1.009
## Error attribution
- minutes MAE 4.97 min · share of absolute error from minutes 34%, from rate 66%
- surprise DNPs (projected ≥10 min, played 0): 13 costing 78.3 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=224, err -0.29, ratio 1.033
- Forward|15-20: n=167, err -0.06, ratio 1.007
- Guard|20-30: n=159, err -0.22, ratio 1.019
- Forward|10-15: n=137, err -0.05, ratio 1.008
- Guard|10-15: n=128, err +0.16, ratio 0.967
- Forward|20-30: n=121, err -0.27, ratio 1.024
- Center|15-20: n=111, err -0.60, ratio 1.058
- Center|10-15: n=90, err -0.46, ratio 1.07
- Forward|<10: n=88, err -0.56, ratio 1.175
- Guard|<10: n=83, err -1.09, ratio 1.322
- Center|<10: n=57, err -1.50, ratio 1.484
- Center|20-30: n=22, err -3.06, ratio 1.226