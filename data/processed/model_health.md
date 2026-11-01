# Model health

No drift flags.

learn: train R4-R7, hold-out R8, R9
- new core + bias: hold-out MAE R8 6.15, R9 6.05 vs current 6.09, 6.05 (gain -0.03)
- new core: hold-out MAE R8 6.09, R9 6.05 vs current 6.09, 6.05 (gain +0.00)
- current core + new bias: hold-out MAE R8 6.15, R9 6.05 vs current 6.09, 6.05 (gain -0.03)
→ kept current core
- shadow challenger 202610290458 ('new core', since R8) - would be promoted after 3 straight newest-round wins
- sd scale kept at 1.096 (hold-out 80% band 80%; candidate ×1.122 → 81%)

## Calibration (walk-forward)
- 80% band holds 80% of outcomes (above p90 14%, below p10 7%; n=1363) → sd scale that would make it 80%: ×1.022
## Error attribution
- minutes MAE 4.95 min · share of absolute error from minutes 32%, from rate 68%
- surprise DNPs (projected ≥10 min, played 0): 12 costing 67.0 projected PIR
## Bias by segment (projected − actual PIR per game; ratio = actual/projected)
- Guard|10-20: n=347, err -0.65, ratio 1.094
- Forward|10-20: n=298, err -0.81, ratio 1.124
- Center|10-20: n=199, err -0.93, ratio 1.115
- Guard|20-30: n=157, err -0.10, ratio 1.009
- Forward|20-30: n=119, err -0.38, ratio 1.034
- Forward|<10: n=86, err -1.16, ratio 1.471
- Guard|<10: n=81, err -2.24, ratio 2.036
- Center|<10: n=55, err -1.99, ratio 1.718
- Center|20-30: n=21, err -2.52, ratio 1.188