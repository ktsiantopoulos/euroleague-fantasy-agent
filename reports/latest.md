## run reason: manual  (deadline 2026-12-03T17:29:00+00:00, 175.46 h away)
## pull-official
E2026: 140 games played, 10 box scores fetched now

## pull-platform
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_15
team: UnderTakers86  credits: 115.7  trades used: 0/4

## pull-external
  fantasyedge: 365 players, 15 columns kept
price base: fantasyedge 238, top100_md1 122, first_seen 10

## build
        games  rows  mismatches
season                         
E2026     140  3350           0
teams mapped: 20; needs attention: 0
method
surname+team        314
UNMATCHED            29
coach                20
surname+any-team      1
team context: 20 clubs · usage: 306 players · FDR: 20 clubs x next 5
price base: fantasyedge 238, top100_md1 122, first_seen 10
matchdays: 38 (one per round) · current MD 15 = R15, nights T1=2026-12-03, 
T2=2026-12-04

## reconcile
player-games compared: 5011
exact matches: 3268 (65.2%)
  no_boxscore_row: 971
  no_player: 723
  MISMATCH: 49

first mismatches:
platform_id  matchday person_code  game_code  platform_pts  official_pir  
official_min team_won  expected_pts   status
      11490        14      014783        136          -2.7          -4.0     
13.416667     True          -3.6 MISMATCH
      11498         6      014731         51           0.0          -1.0     
11.800000     True          -0.9 MISMATCH
      11503        13      014732        124          19.8          17.0     
25.933333     True          18.7 MISMATCH
      11517        14      015162        136          20.0          19.0     
24.333333    False          19.0 MISMATCH
      11527        13      015168        126           1.1           0.0     
13.533333     True           0.0 MISMATCH
      11543         7      014802         61           0.0          -1.0     
11.450000    False          -1.0 MISMATCH
      11546         7      014738         61          14.0          13.0     
16.033333    False          13.0 MISMATCH
      11547        10      014737         98          12.0          11.0     
28.066667    False          11.0 MISMATCH
      11549        14      000898        139           3.0           2.0     
13.950000    False           2.0 MISMATCH
      12145         6      015244         53           4.4           3.0      
9.033333     True           3.3 MISMATCH
      12460        14      014785        132          -2.0          -3.0     
20.750000    False          -3.0 MISMATCH
      13930        14      015396        131           7.0           6.0     
12.250000    False           6.0 MISMATCH
       3769         6      005791         53          15.4          13.0     
16.983333     True          14.3 MISMATCH
       3788         8      011218         80           0.0           2.0     
18.550000     True           2.2 MISMATCH
       3790        14      006540        137          13.0          12.0     
21.900000    False          12.0 MISMATCH

## evaluate
# Projection evaluation

- MD8: 290 players · MAE 4.81 (platform avg_pts baseline 6.03) · bias -0.04 · 
corr 0.608 · above p90 11% / below p10 8% (target 10% each)
- MD9: 298 players · MAE 5.24 (platform avg_pts baseline 5.92) · bias -0.22 · 
corr 0.498 · above p90 11% / below p10 6% (target 10% each)
- MD10: 299 players · MAE 5.28 (platform avg_pts baseline 6.15) · bias +0.32 · 
corr 0.549 · above p90 12% / below p10 6% (target 10% each)
- MD11: 303 players · MAE 5.06 (platform avg_pts baseline 5.82) · bias +0.35 · 
corr 0.553 · above p90 11% / below p10 7% (target 10% each)
- MD12: 308 players · MAE 4.90 (platform avg_pts baseline 5.64) · bias +0.50 · 
corr 0.567 · above p90 8% / below p10 5% (target 10% each)
- MD13: 312 players · MAE 5.16 (platform avg_pts baseline 5.99) · bias +0.43 · 
corr 0.519 · above p90 10% / below p10 7% (target 10% each)
- MD14: 310 players · MAE 4.91 (platform avg_pts baseline 5.79) · bias +0.62 · 
corr 0.533 · above p90 8% / below p10 5% (target 10% each)

## Bias by segment (mean projected − actual; positive = we over-project)
- position: Center -0.6 (n=405), Forward +0.8 (n=745), Guard +0.3 (n=970)
- projected minutes: <10 +0.5 (n=434), 10-20 +0.2 (n=1041), 20-30 +0.3 (n=551), 
30+ +10.6 (n=1)
- price: ≤6 +1.0 (n=564), 6-9 -0.1 (n=835), 9-13 +0.4 (n=538), 13+ -0.3 (n=183)
- availability: doubtful +0.3 (n=196), fit +0.3 (n=1924)

## Biggest misses
- under-projected: Lonnie Walker IV (0→40), Antonio Blakeney (9→38), Moses 
Wright (11→40), Austin Wiley (7→35), Cory Joseph (7→34)
- over-projected: Elijah Bryant (19→-6), Devon Dotson (12→-5), Luca Vildoza 
(10→-7), Jonas Valanciunas (20→3), Tyrese Martin (13→-4)

## Coaches: MAE 10.6, bias +0.1 (n=139)

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
| 11 | 151.7 ± 29.8 | 182.6 | +1.03 | 147.7 | 151.2 (+3.5) | 145.3 | +2.4 / 
+37.3 | 257.9 | 75.3 | 4.4 (Sasha Vezenkov) |
| 12 | 173.6 ± 28.8 | 190.8 | +0.60 | 196.5 | 192.15 (-4.3) | 206.75 | -10.2 / 
-15.9 | 282.8 | 92.0 | 25.3 (Jonas Valanciunas) |
| 13 | 170.1 ± 33.2 | 154.2 | -0.48 | 146.0 | 144.9 (-1.1) | 88.6 | +57.4 / 
+65.7 | 238.6 | 84.3 | 0.0 (Nadir Hifi) |
| 14 | 166.6 ± 32.8 | 120.7 | -1.40 | 171.85 | 163.15 (-8.7) | 157.65 | +14.2 / 
-37.0 | 308.25 | 187.6 | 20.9 (Nadir Hifi) |

Mean z +0.21 (0 = unbiased; |z| > 2 on a matchday is a miss worth reading) · 
mean regret 105.8 · cumulative trade value agent +81.2 / you +64.7
Market variant vs recommendation (matchdays where they differed): 1/4 wins, 
cumulative -10.6 pts · raise MU_PRICE only once this is consistently positive.

## trade backtest
# Trade-discipline replay

Matchdays: 8, 9, 10, 11, 12, 13, 14 · realised gain = recommended squad minus 
no-trade squad, both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +11.6 | +5.4 |
| current defaults | 10 | 4 | +26.9 | +45.4 |
| current defaults | 11 | 4 | +8.3 | +2.4 |
| current defaults | 12 | 4 | +13.8 | -8.8 |

## learn
learn: train R4-R12, hold-out R13, R14
- new core: hold-out MAE R13 6.65, R14 6.22 vs current 6.69, 6.29 (gain +0.06, 
every round)
→ ADOPTED 'new core' (gain +0.06 on every hold-out round)
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.18 → 0.17, RMSE +0.006
- kept tier layer (3 segment(s)): hold-out segment |bias| R13 1.12 → 1.24, R14 
0.66 → 0.57, RMSE +0.027
- sd scale kept at 1.096 (hold-out 80% band 83%; candidate ×1.088 → 83%)
health: no drift flags

## top-100
top-100: 343 roster previews fetched now
# Top-298 managers — matchdays 1–14

## Ownership in the top 298, matchday 14

| player | pos | club | price | top own% | global% | captain # |
|---|---|---|---|---|---|---|
| Sasha Vezenkov | F | OLY | 20.0 | 33 | 51 | 71 |
| Kenan Kamenjas | C | KBA | 6.2 | 33 | 32 | 0 |
| Theo Maledon | G | RMB | 13.8 | 30 | 29 | 7 |
| Moses Wright | C | MIL | 14.2 | 24 | 13 | 21 |
| Nadir Hifi | G | PBB | 16.6 | 24 | 19 | 0 |
| Ibon Navarro | H | CZV | 6.8 | 19 | 21 | 0 |

## backtest
             subset    n  mae_model  corr_model  mae_base_mean  corr_base_mean  
mae_base_last3  corr_base_last3
all dressed players 2572       5.59       0.435           5.71           0.420  
6.00            0.378
projected >= 15 min 1504       6.24       0.317           6.41           0.311  
6.83            0.257
   >= 3 prior games 2421       5.63       0.436           5.70           0.426  
6.02            0.381

## recommend
- Trade discipline: each incoming player must clear 2.0 pts + 0.00×sd; no 
trade-ins with < 3 season games (unless ≥ 2 games and ≥ 20 projected minutes) or
< 70% to play (objective discount on this squad: 8.0; not deducted from the 
expected points).
- Optimiser status: Optimal / Optimal (night-balance relaxed).
