## run reason: pre-deadline (1.3h)  (deadline 2026-11-13T17:29:00+00:00, 1.26 h away)
## pull-official
E2026: 107 games played, 7 box scores fetched now

## pull-platform
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_11
team: UnderTakers86  credits: 110.8  trades used: 4/4

## pull-external
  fantasyedge: 365 players, 15 columns kept
price base: fantasyedge 237, top100_md1 122, first_seen 5

## build
        games  rows  mismatches
season                         
E2026     107  2560           0
teams mapped: 20; needs attention: 0
method
surname+team    305
UNMATCHED        35
coach            20
team context: 20 clubs · usage: 294 players · FDR: 20 clubs x next 5
price base: fantasyedge 237, top100_md1 122, first_seen 5
matchdays: 38 (one per round) · current MD 11 = R11, nights T1=2026-11-11, 
T2=2026-11-12, T3=2026-11-13

## reconcile
player-games compared: 3555
exact matches: 2358 (66.3%)
  no_boxscore_row: 605
  no_player: 571
  MISMATCH: 21

first mismatches:
platform_id  matchday person_code  game_code  platform_pts  official_pir  
official_min team_won  expected_pts   status
      11498         6      014731         51           0.0          -1.0     
11.800000     True          -0.9 MISMATCH
      11543         7      014802         61           0.0          -1.0     
11.450000    False          -1.0 MISMATCH
      11546         7      014738         61          14.0          13.0     
16.033333    False          13.0 MISMATCH
      11547        10      014737         98          12.0          11.0     
28.066667    False          11.0 MISMATCH
      12145         6      015244         53           4.4           3.0      
9.033333     True           3.3 MISMATCH
       3769         6      005791         53          15.4          13.0     
16.983333     True          14.3 MISMATCH
       3788         8      011218         80           0.0           2.0     
18.550000     True           2.2 MISMATCH
       3810         6      009783         52          15.4          13.0     
17.583333     True          14.3 MISMATCH
       3810        10      009783         99           7.0           6.0     
22.266667    False           6.0 MISMATCH
       3857         7      012788         61           7.7           6.0      
9.366667     True           6.6 MISMATCH
       3884         6      010545         52           3.0           2.0     
17.766667    False           2.0 MISMATCH
       3905         6      010781         52           6.6           5.0     
30.416667     True           5.5 MISMATCH
       3907        10      011231         98          11.0           9.0     
19.183333     True           9.9 MISMATCH
       4038         2      006544         20           NaN          -3.0     
11.566667     True          -2.7 MISMATCH
       4670        10      013389         97          11.0           9.0     
21.366667     True           9.9 MISMATCH

## evaluate
# Projection evaluation

- MD8: 289 players · MAE 4.81 (platform avg_pts baseline 6.02) · bias -0.06 · 
corr 0.608 · above p90 11% / below p10 8% (target 10% each)
- MD9: 298 players · MAE 5.24 (platform avg_pts baseline 5.92) · bias -0.22 · 
corr 0.498 · above p90 11% / below p10 6% (target 10% each)
- MD10: 299 players · MAE 5.28 (platform avg_pts baseline 6.15) · bias +0.32 · 
corr 0.549 · above p90 12% / below p10 6% (target 10% each)

## Bias by segment (mean projected − actual; positive = we over-project)
- position: Center -1.0 (n=166), Forward +0.5 (n=315), Guard +0.1 (n=405)
- projected minutes: <10 -0.0 (n=180), 10-20 +0.1 (n=454), 20-30 -0.1 (n=217)
- price: ≤6 +0.8 (n=222), 6-9 -0.3 (n=352), 9-13 +0.1 (n=230), 13+ -1.1 (n=82)
- availability: doubtful +0.3 (n=69), fit -0.0 (n=817)

## Biggest misses
- under-projected: Lonnie Walker IV (0→40), Antonio Blakeney (9→38), Austin 
Wiley (7→35), Nadir Hifi (16→43), Theo Maledon (16→38)
- over-projected: Elijah Bryant (19→-6), Tyrese Martin (13→-4), Scottie Wilbekin
(11→-5), Tyson Ward (13→-2), Sylvain Francisco (14→-1)

## Coaches: MAE 10.5, bias +0.3 (n=58)

## scorecard
# Decision scorecard

| MD | expected | actual | z | agent rec (actual) | market variant (actual) | no
trades (actual) | trades: agent / you | hindsight | regret | captain regret |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 150.4 ± 28.5 | 155.2 | +0.17 | 154.05 | — | 163.85 | -9.8 / -8.7 | 248.25 
| 93.1 | 0.0 (Sasha Vezenkov) |
| 9 | 147.6 ± 31.3 | 166.6 | +0.61 | 158.0 | — | 164.9 | -6.9 / +1.7 | 272.3 | 
105.8 | 14.3 (Sasha Vezenkov) |
| 10 | 148.7 ± 30.4 | 176.9 | +0.93 | 189.4 | — | 155.35 | +34.1 / +21.6 | 279.6
| 102.7 | 0.0 (Sasha Vezenkov) |

Mean z +0.57 (0 = unbiased; |z| > 2 on a matchday is a miss worth reading) · 
mean regret 100.5 · cumulative trade value agent +17.4 / you +14.6

## trade backtest
# Trade-discipline replay

Matchdays: 8, 9, 10 · realised gain = recommended squad minus no-trade squad, 
both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +15.2 | +4.3 |
| current defaults | 10 | 4 | +25.3 | +34.1 |
| no discipline | 8 | 4 | +14.7 | -9.8 |
| no discipline | 9 | 4 | +11.3 | -6.9 |

## learn
learn: train R4-R9, hold-out R10, R11
- new core: hold-out MAE R10 6.91, R11 6.24 vs current 6.91, 6.21 (gain -0.02)
→ kept current core
- shadow challenger 202611131616 ('new core', since R11) - would be promoted 
after 3 straight newest-round wins
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.24 → 0.25, RMSE +0.008
- kept tier layer (3 segment(s)): hold-out segment |bias| R10 1.47 → 1.57, R11 
1.18 → 1.58, RMSE +0.052
- sd scale kept at 1.096 (hold-out 80% band 80%; candidate ×1.105 → 80%)
DRIFT: model lost to a naive baseline in R10 and R11

## backtest
             subset    n  mae_model  corr_model  mae_base_mean  corr_base_mean  
mae_base_last3  corr_base_last3
all dressed players 1796       5.61       0.429           5.76           0.411  
6.05            0.374
projected >= 15 min 1040       6.26       0.324           6.46           0.310  
6.84            0.258
   >= 3 prior games 1670       5.65       0.432           5.76           0.420  
6.06            0.379

## recommend
one club; 1 point per credit for bench players under 6.0.
- Trade discipline: each incoming player must clear 2.0 pts + 0.00×sd; no 
trade-ins with < 3 season games or < 70% to play (objective discount on this 
squad: 8.0; not deducted from the expected points).
- Optimiser status: Optimal / Optimal (night-balance relaxed).
