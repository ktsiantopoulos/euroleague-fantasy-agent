## run reason: daily  (deadline 2026-11-04T19:44:00+00:00, 10.69 h away)
## pull-official
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/requests/models.py", line 1116, in json
    return complexjson.loads(self.text, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/json/decoder.py", line 338, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/json/decoder.py", line 356, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.15/x64/bin/elfa", line 6, in <module>
    sys.exit(app())
             ^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/main.py", line 1154, in __call__
    raise e
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/main.py", line 1137, in __call__
    return get_command(self)(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/_click/core.py", line 802, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/core.py", line 1197, in main
    return _main(
           ^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/core.py", line 187, in _main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/core.py", line 1119, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/_click/core.py", line 741, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/_click/core.py", line 483, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/typer/main.py", line 1524, in wrapper
    return callback(**use_params)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/src/elfa/cli.py", line 26, in pull_official
    played, fetched = pull_season(client, season)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/src/elfa/ingest/euroleague.py", line 58, in pull_season
    games = client.games(season)
            ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/src/elfa/ingest/euroleague.py", line 32, in games
    return self._get(f"/v2/competitions/E/seasons/{season}/games")["data"]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/src/elfa/ingest/euroleague.py", line 29, in _get
    return r.json()
           ^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/requests/models.py", line 1120, in json
    raise RequestsJSONDecodeError(e.msg, e.doc, e.pos)
requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

## pull-platform
pulled -> 
/home/runner/work/euroleague-fantasy-agent/euroleague-fantasy-agent/data/raw/fan
taking/md_10
team: UnderTakers86  credits: 108.6  trades used: 0/4

## pull-external
  fantasyedge: 376 players, 15 columns kept
price base: fantasyedge 237, top100_md1 122, first_seen 5

## build
        games  rows  mismatches
season                         
E2026      90  2153           0
teams mapped: 20; needs attention: 0
method
surname+team    299
UNMATCHED        44
coach            20
team context: 20 clubs · usage: 288 players · FDR: 20 clubs x next 5
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

- MD9: 298 players · MAE 5.24 (platform avg_pts baseline 5.92) · bias -0.22 · 
corr 0.498 · above p90 11% / below p10 6% (target 10% each)

## Bias by segment (mean projected − actual; positive = we over-project)
- position: Center -0.3 (n=56), Forward +0.1 (n=105), Guard -0.4 (n=137)
- projected minutes: <10 +0.1 (n=61), 10-20 -0.4 (n=152), 20-30 -0.0 (n=74)
- price: ≤6 +0.8 (n=74), 6-9 -1.1 (n=117), 9-13 +0.1 (n=80), 13+ -0.2 (n=27)
- availability: doubtful -1.4 (n=21), fit -0.1 (n=277)

## Biggest misses
- under-projected: Lonnie Walker IV (0→40), Theo Maledon (16→38), Tyty 
Washington (10→32), Filip Petrusev (8→29), Nadir Hifi (13→33)
- over-projected: Elijah Bryant (19→-6), Tyrese Martin (13→-4), Tadas 
Sedekerskis (13→0), Anthony Brown (11→-2), Mfiondu Kabengele (22→9)

## Coaches: MAE 9.8, bias +0.4 (n=19)

## scorecard
# Decision scorecard

| MD | expected | actual | z | agent rec (actual) | no trades (actual) | trades:
agent / you | hindsight | regret | captain regret |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 147.6 ± 31.3 | 166.6 | +0.61 | 158.0 | 164.9 | -6.9 / +1.7 | 272.3 | 105.8
| 14.3 (Sasha Vezenkov) |

Mean z +0.61 (0 = unbiased; |z| > 2 on a matchday is a miss worth reading) · 
mean regret 105.8 · cumulative trade value agent -6.9 / you +1.7

## learn
learn: train R4-R7, hold-out R8, R9
- new core + bias: hold-out MAE R8 6.15, R9 6.05 vs current 6.09, 6.05 (gain 
-0.03)
- new core: hold-out MAE R8 6.09, R9 6.05 vs current 6.09, 6.05 (gain +0.00)
- current core + new bias: hold-out MAE R8 6.15, R9 6.05 vs current 6.09, 6.05 
(gain -0.03)
→ kept current core
- shadow challenger 202610290458 ('new core', since R8) - would be promoted 
after 3 straight newest-round wins
- sd scale kept at 1.096 (hold-out 80% band 80%; candidate ×1.122 → 81%)
health: no drift flags

## top-100
top-100: 0 roster previews fetched now
# Top-180 managers — matchdays 1–9

## Ownership in the top 180, matchday 9

| player | pos | club | price | top own% | global% | captain # |
|---|---|---|---|---|---|---|
| Sasha Vezenkov | F | OLY | 18.4 | 52 | 46 | 21 |
| Theo Maledon | G | RMB | 12.1 | 49 | 12 | 68 |
| Aliou Diarra | C | VIR | 10.0 | 48 | 36 | 0 |
| Ibon Navarro | H | CZV | 7.2 | 42 | 11 | 0 |
| Andres Feliz | G | RMB | 8.6 | 31 | 31 | 0 |
| Yam Madar | G | MTA | 10.2 | 25 | 13 | 0 |

## backtest
             subset    n  mae_model  corr_model  mae_base_mean  corr_base_mean  
mae_base_last3  corr_base_last3
all dressed players 1395       5.55       0.420           5.78           0.400  
6.03            0.367
projected >= 15 min  792       6.14       0.309           6.43           0.288  
6.78            0.245
   >= 3 prior games 1295       5.58       0.422           5.78           0.405  
6.05            0.369

## recommend
- Elite-consensus tilt: expected points scaled by up to +4% at 100% top-100 
ownership (raw model value kept as md_pts_model).
- Soft rules from the top-100 study: 3 points penalty per player above 3 from 
one club; 1 point per credit for bench players under 6.0.
- Optimiser status: Optimal / Optimal (night-balance relaxed).
