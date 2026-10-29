## run reason: manual  (deadline 2026-10-28T17:29:00+00:00, -11.47 h away)
## pull-official
E2026: 80 games played, 0 box scores fetched now

## pull-platform
  ! platform still reports MD 8 (all games played) - rolled over to MD 9, deadline 2026-10-29 18:59 UTC from the schedule
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_09
team: UnderTakers86  credits: 107.3  trades used: 0/4

## pull-external
  fantasyedge: 373 players, 15 columns kept
price base: fantasyedge 237, top100_md1 122, first_seen 3

## build
        games  rows  mismatches
season                         
E2026      80  1915           0
teams mapped: 20; needs attention: 0
method
surname+team    298
UNMATCHED        44
coach            19
team context: 20 clubs · usage: 288 players · FDR: 20 clubs x next 5
price base: fantasyedge 237, top100_md1 122, first_seen 3
matchdays: 38 (one per round) · current MD 8 = R8, nights T1=2026-10-27, 
T2=2026-10-28, T1=2026-10-29, T2=2026-10-30

## reconcile
player-games compared: 2834
exact matches: 1881 (66.4%)
  no_player: 513
  no_boxscore_row: 425
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
no completed matchday with a pre-lock snapshot yet (first one: MD 9) - 
evaluation starts once it is played

## scorecard
no matchday with a pre-lock decision snapshot and final results yet (first one: 
MD 9)

## learn
learn: train R4-R6, hold-out R7, R8
- new core + bias: hold-out MAE R7 6.45, R8 6.13 vs current 6.46, 6.11 (gain 
-0.01)
- new core: hold-out MAE R7 6.45, R8 6.09 vs current 6.46, 6.11 (gain +0.01, 
every round)
- current core + new bias: hold-out MAE R7 6.40, R8 6.16 vs current 6.46, 6.11 
(gain +0.00)
→ kept current core
- shadow challenger 202610290458 ('new core', since R8) - would be promoted 
after 3 straight newest-round wins
→ sd scale 1.0 → 1.096 (hold-out 80% band 73% → 77%)
health: no drift flags

## top-100
top-100: 0 roster previews fetched now
# Top-140 managers — matchdays 1–8

## Ownership in the top 140, matchday 8

| player | pos | club | price | top own% | global% | captain # |
|---|---|---|---|---|---|---|
| Theo Maledon | G | RMB | 11.9 | 59 | 35 | 0 |
| Andres Feliz | G | RMB | 8.6 | 56 | 34 | 0 |
| Sasha Vezenkov | F | OLY | 18.4 | 56 | 45 | 36 |
| Aliou Diarra | C | VIR | 9.8 | 49 | 36 | 0 |
| Mfiondu Kabengele | C | DUB | 15.6 | 47 | 17 | 35 |
| Elijah Bryant | G | HTA | 17.2 | 39 | 13 | 14 |

## backtest
             subset    n  mae_model  corr_model  mae_base_mean  corr_base_mean  
mae_base_last3  corr_base_last3
all dressed players 1159       5.56       0.412           5.81           0.397  
6.02            0.366
projected >= 15 min  651       6.18       0.312           6.49           0.296  
6.80            0.253
   >= 3 prior games 1076       5.59       0.412           5.81           0.402  
6.04            0.368

## recommend
- Elite-consensus tilt: expected points scaled by up to +4% at 100% top-100 
ownership (raw model value kept as md_pts_model).
- Soft rules from the top-100 study: 3 points penalty per player above 3 from 
one club; 1 point per credit for bench players under 6.0.
- Optimiser status: Optimal / Optimal (night-balance relaxed).
