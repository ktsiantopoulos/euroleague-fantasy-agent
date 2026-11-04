# Model health

No drift flags.

learn: train R4-R7, hold-out R8, R9
- new core: hold-out MAE R8 6.09, R9 6.05 vs current 6.09, 6.05 (gain +0.00)
→ kept current core
- shadow challenger 202610290458 ('new core', since R8) - would be promoted after 3 straight newest-round wins
→ ADOPTED bias layer (9 segment(s)): hold-out mean |bias| 0.86 → 0.41, RMSE -0.044
- sd scale kept at 1.096 (hold-out 80% band 80%; candidate ×1.113 → 81%)

## Calibration (walk-forward)
- 80% band holds 80% of outcomes (above p90 13%, below p10 8%; n=1363) → sd scale that would make it 80%: ×1.009
## Error attribution
- minutes MAE 4.95 min · share of absolute error from minutes 34%, from rate 66%
- surprise DNPs (projected ≥10 min, played 0): 12 costing 71.1 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|15-20: n=222, err -0.20, ratio 1.022
- Forward|15-20: n=163, err +0.03, ratio 0.996
- Guard|20-30: n=157, err -0.10, ratio 1.009
- Forward|10-15: n=135, err -0.13, ratio 1.021
- Guard|10-15: n=125, err +0.08, ratio 0.984
- Forward|20-30: n=119, err -0.38, ratio 1.034
- Center|15-20: n=110, err -0.58, ratio 1.057
- Center|10-15: n=89, err -0.32, ratio 1.048
- Forward|<10: n=86, err -0.46, ratio 1.145
- Guard|<10: n=81, err -0.94, ratio 1.273
- Center|<10: n=55, err -1.63, ratio 1.519
- Center|20-30: n=21, err -2.52, ratio 1.188