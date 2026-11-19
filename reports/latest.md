## run reason: manual  (deadline 2026-11-19T17:14:00+00:00, 2.75 h away)
## pull-official
E2026: 120 games played, 0 box scores fetched now

## pull-platform
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_13
team: UnderTakers86  credits: 115.5  trades used: 0/4

## pull-external
  fantasyedge: 365 players, 15 columns kept
price base: fantasyedge 237, top100_md1 122, first_seen 8

## build
        games  rows  mismatches
season                         
E2026     120  2871           0
teams mapped: 20; needs attention: 0
method
surname+team        311
UNMATCHED            30
coach                20
surname+any-team      1
team context: 20 clubs · usage: 300 players · FDR: 20 clubs x next 5
price base: fantasyedge 237, top100_md1 122, first_seen 8
matchdays: 38 (one per round) · current MD 13 = R13, nights T1=2026-11-19, 
T2=2026-11-20

## reconcile
player-games compared: 4285
exact matches: 2835 (66.2%)
  no_boxscore_row: 794
  no_player: 633
  MISMATCH: 23

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

## Bias by segment (mean projected − actual; positive = we over-project)
- position: Center -1.0 (n=284), Forward +0.7 (n=530), Guard +0.3 (n=684)
- projected minutes: <10 +0.3 (n=314), 10-20 +0.1 (n=745), 20-30 +0.2 (n=376)
- price: ≤6 +1.0 (n=387), 6-9 -0.1 (n=595), 9-13 +0.2 (n=386), 13+ -0.8 (n=130)
- availability: doubtful +0.6 (n=128), fit +0.1 (n=1370)

## Biggest misses
- under-projected: Lonnie Walker IV (0→40), Antonio Blakeney (9→38), Austin 
Wiley (7→35), Nadir Hifi (16→43), Johannes Thiemann (9→34)
- over-projected: Elijah Bryant (19→-6), Luca Vildoza (10→-7), Tyrese Martin 
(13→-4), Scottie Wilbekin (11→-5), Elie Okobo (14→-2)

## Coaches: MAE 10.4, bias +0.1 (n=99)

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

Mean z +0.67 (0 = unbiased; |z| > 2 on a matchday is a miss worth reading) · 
mean regret 93.8 · cumulative trade value agent +9.6 / you +36.0
Market variant vs recommendation (matchdays where they differed): 1/2 wins, 
cumulative -0.8 pts · raise MU_PRICE only once this is consistently positive.

## trade backtest
# Trade-discipline replay

Matchdays: 8, 9, 10, 11, 12 · realised gain = recommended squad minus no-trade 
squad, both on actual points

| setting | MD | trades | predicted gain | realised gain |
|---|---|---|---|---|
| current defaults | 8 | 4 | +17.4 | -2.6 |
| current defaults | 9 | 4 | +15.2 | +4.3 |
| current defaults | 10 | 4 | +25.3 | +34.1 |
| current defaults | 11 | 4 | +8.3 | +2.4 |
| current defaults | 12 | 4 | +12.5 | -10.2 |

## learn
learn: train R4-R10, hold-out R11, R12
- new core: hold-out MAE R11 6.18, R12 5.81 vs current 6.20, 5.81 (gain +0.01)
→ kept current core
- shadow challenger 202611131616 ('new core', since R11) - would be promoted 
after 3 straight newest-round wins
- kept bias layer (9 segment(s)): hold-out mean |bias| 0.13 → 0.15, RMSE -0.002
- kept tier layer (3 segment(s)): hold-out segment |bias| R11 1.19 → 1.33, R12 
1.40 → 1.23, RMSE -0.015
- sd scale kept at 1.096 (hold-out 80% band 82%; candidate ×1.115 → 83%)
health: no drift flags

## top-100
top-100: 0 roster previews fetched now
# Top-261 managers — matchdays 1–12

## Ownership in the top 261, matchday 12

| player | pos | club | price | top own% | global% | captain # |
|---|---|---|---|---|---|---|
| Sasha Vezenkov | F | OLY | 19.2 | 38 | 49 | 90 |
| Andres Feliz | G | RMB | 9.7 | 33 | 34 | 0 |
| Theo Maledon | G | RMB | 12.9 | 30 | 18 | 6 |
| Aliou Diarra | C | VIR | 10.8 | 25 | 32 | 0 |
| Alberto Abalde | F | RMB | 6.1 | 24 | 18 | 0 |
| Saras Jasikevicius | H | FBT | 8.3 | 23 | 12 | 0 |

## backtest
             subset    n  mae_model  corr_model  mae_base_mean  corr_base_mean  
mae_base_last3  corr_base_last3
all dressed players 2099       5.60       0.433           5.72           0.419  
6.01            0.381
projected >= 15 min 1222       6.21       0.334           6.37           0.322  
6.78            0.269
   >= 3 prior games 1963       5.62       0.439           5.70           0.430  
6.01            0.388

## recommend
one club; 1 point per credit for bench players under 6.0.
- Trade discipline: each incoming player must clear 2.0 pts + 0.00×sd; no 
trade-ins with < 3 season games or < 70% to play (objective discount on this 
squad: 8.0; not deducted from the expected points).
- Optimiser status: Optimal / Optimal.
