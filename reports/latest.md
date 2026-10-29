## run reason: manual  (deadline 2026-10-28T17:29:00+00:00, -10.68 h away)
## pull-official
E2026: 80 games played, 4 box scores fetched now

## pull-platform
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_08
team: UnderTakers86  credits: 107.3  trades used: 4/4

## pull-external
  fantasyedge: 373 players, 15 columns kept
price base: fantasyedge 237, top100_md1 122, first_seen 3

## build
        games  rows  mismatches
season                         
E2026      80  1915           0
teams mapped: 20; needs attention: 0
method
surname+team    297
UNMATCHED        44
coach            20
team context: 20 clubs · usage: 288 players · FDR: 20 clubs x next 5
price base: fantasyedge 237, top100_md1 122, first_seen 3
matchdays: 38 (one per round) · current MD 8 = R8, nights T1=2026-10-27, 
T2=2026-10-28

## reconcile
player-games compared: 2475
exact matches: 1653 (66.8%)
  no_player: 443
  no_boxscore_row: 365
  MISMATCH: 14

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
no completed matchday with a stored projection yet - evaluation starts after the
first played matchday

## learn
learn: hold-out R8 MAE current 6.11 vs candidate 6.10 (w=(0.2, 0.3, 0.5), λ=0.3,
γ=1.0) → kept current

## top-100
top-100: 280 roster previews fetched now
# Top-140 managers — matchdays 1–7

## Ownership in the top 140, matchday 7

| player | pos | club | price | top own% | global% | captain # |
|---|---|---|---|---|---|---|
| Aliou Diarra | C | VIR | 9.3 | 87 | 36 | 7 |
| Theo Maledon | G | RMB | 12.3 | 79 | 35 | 0 |
| Andres Feliz | G | RMB | 8.2 | 71 | 34 | 0 |
| Sasha Vezenkov | F | OLY | 18.4 | 70 | 45 | 52 |
| Tomas Masiulis | H | ZAL | 6.3 | 66 | 12 | 0 |
| Elijah Bryant | G | HTA | 17.4 | 51 | 13 | 0 |

## backtest
             subset   n  mae_model  corr_model  mae_base_mean  corr_base_mean  
mae_base_last3  corr_base_last3
all dressed players 935       5.52       0.412           5.82           0.389   
5.97            0.371
projected >= 15 min 512       6.20       0.311           6.58           0.284   
6.80            0.262
   >= 3 prior games 857       5.55       0.416           5.82           0.398   
5.98            0.378

## recommend
- Elite-consensus tilt: expected points scaled by up to +4% at 100% top-100 
ownership (raw model value kept as md_pts_model).
- Soft rules from the top-100 study: 3 points penalty per player above 3 from 
one club; 1 point per credit for bench players under 6.0.
- Optimiser status: Optimal / Optimal.
