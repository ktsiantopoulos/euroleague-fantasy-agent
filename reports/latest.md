## run reason: pre-deadline (1.8h)  (deadline 2026-11-05T17:14:00+00:00, 1.83 h away)
## pull-official
E2026: 91 games played, 1 box scores fetched now

## pull-platform
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_10
team: UnderTakers86  credits: 108.6  trades used: 4/4

## pull-external
  fantasyedge: 376 players, 15 columns kept
price base: fantasyedge 237, top100_md1 122, first_seen 5

## build
        games  rows  mismatches
season                         
E2026      91  2177           0
teams mapped: 20; needs attention: 0
method
surname+team    299
UNMATCHED        41
coach            20
team context: 20 clubs · usage: 289 players · FDR: 20 clubs x next 5
price base: fantasyedge 237, top100_md1 122, first_seen 5
matchdays: 38 (one per round) · current MD 8 = R8, nights T1=2026-10-27, 
T2=2026-10-28, T1=2026-10-29, T2=2026-10-30, T1=2026-11-04, T2=2026-11-05, 
T3=2026-11-06

## reconcile
player-games compared: 3195
exact matches: 2125 (66.5%)
  no_player: 561
  no_boxscore_row: 494
  MISMATCH: 15

first mismatches:
platform_id  matchday person_code  game_code  platform_pts  official_pir  
official_min team_won  expected_pts   status
      11498         6      014731         51           0.0          -1.0     
11.800000     True          -0.9 MISMATCH
      11543         7      014802         61           0.0          -1.0     
11.450000    False          -1.0 MISMATCH
      11546         7      014738         61          14.0          13.0     
16.033333    False          13.0 MISMATCH
      12145         6      015244         53           4.4           3.0      
9.033333     True           3.3 MISMATCH
       3769         6      005791         53          15.4          13.0     
16.983333     True          14.3 MISMATCH
       3788         8      011218         80           0.0           2.0     
18.550000     True           2.2 MISMATCH
       3810         6      009783         52          15.4          13.0     
17.583333     True          14.3 MISMATCH
       3857         7      012788         61           7.7           6.0      
9.366667     True           6.6 MISMATCH
       3884         6      010545         52           3.0           2.0     
17.766667    False           2.0 MISMATCH
       3905         6      010781         52           6.6           5.0     
30.416667     True           5.5 MISMATCH
       4038         2      006544         20           NaN          -3.0     
11.566667     True          -2.7 MISMATCH
       4675         7      013402         61          -2.7          -4.0      
7.016667     True          -3.6 MISMATCH
       7209         6      014009         54           9.0           8.0     
20.616667    False           8.0 MISMATCH
       7268         6      013929         51          20.0          19.0     
20.083333    False          19.0 MISMATCH
       8808         4      014207         38           7.7           5.0     
19.366667     True           5.5 MISMATCH

## evaluate
# Projection evaluation

- MD8: 289 players · MAE 4.81 (platform avg_pts baseline 6.02) · bias -0.06 · 
corr 0.608 · above p90 11% / below p10 8% (target 10% each)
- MD9: 298 players · MAE 5.24 (platform avg_pts baseline 5.92) · bias -0.22 · 
corr 0.498 · above p90 11% / below p10 6% (target 10% each)

## Bias by segment (mean projected − actual; positive = we over-project)
- position: Center -1.3 (n=109), Forward +0.4 (n=209), Guard -0.1 (n=269)
- projected minutes: <10 -0.1 (n=119), 10-20 -0.0 (n=304), 20-30 -0.4 (n=142)
- price: ≤6 +0.9 (n=144), 6-9 -0.8 (n=234), 9-13 +0.2 (n=154), 13+ -1.0 (n=55)
- availability: doubtful -0.5 (n=41), fit -0.1 (n=546)

## Biggest misses
- under-projected: Lonnie Walker IV (0→40), Antonio Blakeney (9→38), Theo 
Maledon (16→38), Tyty Washington (10→32), Donta Hall (4→25)
- over-projected: Elijah Bryant (19→-6), Tyrese Martin (13→-4), Sylvain 
Francisco (14→-1), Scottie Wilbekin (14→-1), Marcus Carr (13→-1)

## Coaches: MAE 9.8, bias +0.6 (n=38)

## scorecard
# Decision scorecard

| MD | expected | actual | z | agent rec (actual) | no trades (actual) | trades:
agent / you | hindsight | regret | captain regret |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 150.4 ± 28.5 | 155.2 | +0.17 | 154.05 | 163.85 | -9.8 / -8.7 | 248.25 | 
93.1 | 0.0 (Sasha Vezenkov) |
| 9 | 147.6 ± 31.3 | 166.6 | +0.61 | 158.0 | 164.9 | -6.9 / +1.7 | 272.3 | 105.8
| 14.3 (Sasha Vezenkov) |

Mean z +0.39 (0 = unbiased; |z| > 2 on a matchday is a miss worth reading) · 
mean regret 99.4 · cumulative trade value agent -16.7 / you -7.0

## trade backtest
# Trade-discipline replay

Matchdays: 8, 9 · realised gain = recommended squad minus no-trade squad, both 
on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +15.2 | +4.3 |
| no discipline | 8 | 4 | +14.7 | -9.8 |
| no discipline | 9 | 4 | +11.3 | -6.9 |


## learn
learn: train R4-R8, hold-out R9, R10
- new core: hold-out MAE R9 6.02, R10 8.51 vs current 6.06, 8.29 (gain -0.09)
→ kept current core
- shadow challenger 202611051527 ('new core', since R10) - would be promoted 
after 3 straight newest-round wins
- kept bias layer (8 segment(s)): hold-out mean |bias| 1.70 → 1.71, RMSE -0.003
- sd scale kept at 1.096 (hold-out 80% band 81%; candidate ×1.12 → 82%)
health: no drift flags

## backtest
             subset    n  mae_model  corr_model  mae_base_mean  corr_base_mean  
mae_base_last3  corr_base_last3
all dressed players 1419       5.61       0.420           5.80           0.402  
6.05            0.370
projected >= 15 min  804       6.19       0.313           6.45           0.293  
6.80            0.249
   >= 3 prior games 1315       5.65       0.422           5.81           0.408  
6.07            0.373

## recommend
one club; 1 point per credit for bench players under 6.0.
- Trade discipline: each incoming player must clear 2.0 pts + 0.00×sd; no 
trade-ins with < 3 season games or < 70% to play (objective discount on this 
squad: 8.0; not deducted from the expected points).
- Optimiser status: Optimal / Optimal (night-balance relaxed).
