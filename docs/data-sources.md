# EuroLeague Fantasy Agent — Data Source Discovery (24 Oct 2026)

## 1. Fantasy platform backend (Dunkest "Fantaking" engine)

- Base URL: `https://fantaking-api.dunkest.com`
- Auth: `Authorization: Bearer <token>` + `Accept: application/json`
- Token location in browser: `localStorage["flutter.authToken"]` (JSON string, 56 chars, provider `euroLeagueSSO`).
  Copy it from Chrome DevTools → Application → Local Storage → euroleaguefantasy.euroleaguebasketball.net.
  Store it in `.env` as `FANTAKING_TOKEN`. Never commit it.
- Identifiers for this season:
  | Thing | Value |
  |---|---|
  | game_id (EuroLeague Fantasy Challenge) | 7 |
  | league_id (EuroLeague) | 10 |
  | players_list_id / competition_id / schedule_id | 49 |
  | My fantasy team id (UnderTakers86, Classic) | 2787922 |
  | Current matchday (MD 8, double round) | id 1535, deadline 2026-10-27T15:59Z |
  | Previous matchday (MD 7) | id 1534 |

### Endpoints verified (all GET)
| Purpose | Path | Notes |
|---|---|---|
| Game config (positions, formations, game modes) | `/api/v1/games/7/config` | static |
| League config (rules, teams, 38 matchdays, current matchday/round) | `/api/v1/leagues/10/config` | **source of truth for rules** |
| My teams | `/api/v1/user/fantasy-teams?league=10&game_mode=1` | |
| My team state for a matchday (credits, trades, pts) | `/api/v1/fantasy-teams/{team}/matchdays/{md}` | `credits`, `trades`, `max_num_trades_per_matchday`, `wildcards` |
| My roster for a matchday | `/api/v1/fantasy-teams/{team}/matchdays/{md}/roster` | 11 players, `quotation`, `is_captain`, `active`, `court_position`, `opponent`, `probability_of_playing`, `is_injured` |
| **Player market** (358 players, paginated) | `/api/v1/players-lists/49/matchdays/{md}/players?per_page=100&page=N&sort_by=quotation&sort_order=desc` | fields: `id, first_name, last_name, quotation, avg_pts, popularity, position{id,name}, team{abbr,position home/away}, opponent, round, is_injured, probability_of_playing, is_on_fire` |
| Player profile | `/api/v1/players/{id}/profile?league=10&lang=en` | |
| Player fantasy pts per matchday (with stat breakdown) | `/api/v1/players/{id}/fantasy-pts?league=10&matchday={md}&lang=en` | **gives per-stat fantasy points → scoring formula** |
| Player upcoming matches | `/api/v1/players/{id}/upcoming-matches?league=10` | |
| Player trend (last matchdays) | `/api/v1/players/{id}/trend?league=10` | |
| Player match log | `/api/v1/basketball/leagues/10/players/{id}/match-log/rendered` | |

## 2. Rules (from `/leagues/10/config` → `game_modes_configs[game_mode_id=1]`)
- Roster: 11 = 5 starters + 5 bench + 1 head coach (`num_players_per_team` 11)
- Positions: Guard 4, Forward 4, Center 2, Head Coach 1
- Max 6 players from the same club
- Captain multiplier ×2
- Trades: 4 per matchday (`max_num_trades_per_matchday`), cost 0, no extra credits
- Budget: 100 credits at creation; current team sits at 105.9 (price appreciation)
- Position ids: Guard 28, Forward 29, Center 30, Head Coach 31
- Open items to verify: bench scoring / auto-substitution rule (`max_auto_substitutions` is null), coach scoring formula, double-round handling (MD 8 has `num_rounds: 2`).

## 3. Scoring (verified against official box scores, MD 1-7, 2,474 player-games)
Base = PIR: `pts +1, reb +1, ast +1, stl +1, blk +1, fouls drawn +1, tov −1, pf −1, fg_missed −1, ft_missed −1, blocks received −1`
(official API `valuation` matched our recomputation in 11,218 of 11,218 rows).
**Win bonus: +10% of |PIR| when the player's team wins** (e.g. 19 → 20.9; −5 → −4.5). DNP = 0.
Coach: margin buckets win 1-10 +10, 11-20 +20, 21+ +25 (user); loss 1-10 −5, 11-20 −10, 21+ −20. Bench slots score 50%; 6th man 100%; no auto-substitution.

## 4. Official stats API (public, no auth)
- Base: `https://api-live.euroleague.net/v3`
- Season code: `E2026` (2026-27). Only the current season is pulled and used; no prior-season data is kept in the repo.
- Player traditional/advanced stats: `/competitions/E/statistics/players/traditional?seasonMode=Range&fromSeasonCode=E2026&toSeasonCode=E2026`
- Game box score: `/competitions/E/seasons/E2026/games/{gameCode}/stats`
- Schedule: `/competitions/E/seasons/E2026/games`
- Python wrappers: `pip install euroleague-api` or `py-euroleague`

## 5. Team abbreviations (20 clubs)
EFS, MIL, BJK, CZV, DUB, BAR, BAY, FBT, HTA, KBA, ASV, MTA, OLY, PAO, PBB, PAR, RMB, VBC, VIR, ZAL

## 6. Current roster snapshot (MD 8)
Kabengele C DUB 15.6 · Diarra C VIR 9.8 · Ndiaye F OLY 8.9 · Vezenkov F OLY 18.4 (C) · Nunn G PAO 13.7 · Feliz G RMB 8.6 · Maledon G RMB 11.9 · Lakic F PAR 4.0 · Ugurlu G BJK 4.0 · Papanikolaou F OLY 4.1 · Masiulis HC ZAL 6.6
Credits 105.9 · Total pts 1012.5 · Trades used 0/4

## 7. Risks
- Token lifetime unknown — expect to refresh manually when the agent gets 401.
- Rate limits unknown — pull the market once per matchday (4 pages at per_page=100), player detail only for shortlist.
- Dunkest ToS: personal, read-only use only; no automated trades.

## 8. Rules verified from the official rulebook and EuroLeague articles (24 Oct 2026)
Sources: Fantaking rulebook (fantaking.gitbook.io/euroleague-fantasy-challenge-rules — Initial team, Managing your team,
Players scoring, Coach scoring), euroleaguebasketball.net "In-round management is critical", Dunkest "How the Classic Mode works".
- Roster 2 C / 4 F / 4 G / 1 HC; budget 100 (+0.3 per round for late registration); max 6 per club.
- Formations: 2-2-1, 1-2-2, 2-1-2, 1-3-1, 3-1-1 (G-F-C). Captain from the starting five, x2. Sixth man 100%, bench 50%, coach 100%.
- A Round is split into Turns (game nights). Between turns: field↔bench swaps and captain changes allowed only if the
  incoming player has NOT yet played; a demoted player's score is halved; formation can change; a reset button exists.
- Trades: 4 per round (coach counts as one of the 4). Unlimited-trade windows 2026-27: after R6 (Oct 16-21), R13 (Nov 21-24),
  R18 (Dec 19-22), R23 (Jan 16-21), R28 (Feb 13-Mar 4), R34 (Mar 27-31). Unlimited in play-ins/playoffs/F4.
- Postponed game with average score awarded: captain does NOT double.
- House rule (user): never a center as sixth man.
