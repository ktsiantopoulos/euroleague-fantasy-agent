"""elfa command-line entry point."""
from __future__ import annotations

import json

import typer
from rich import print as rprint

from elfa.config import PROCESSED, Settings


def _redact(msg: str, secret: str) -> str:
    return msg.replace(secret, "***") if secret else msg


app = typer.Typer(help="EuroLeague Fantasy Agent", no_args_is_help=True, pretty_exceptions_enable=False)


@app.command("pull-official")
def pull_official(seasons: str = typer.Option("E2026", help="comma-separated season codes")):
    """Fetch schedule + box scores for played games (incremental) from the public EuroLeague API."""
    from elfa.ingest.euroleague import EuroleagueClient, pull_season

    client = EuroleagueClient(Settings.public_only())
    for season in [s.strip() for s in seasons.split(",") if s.strip()]:
        played, fetched = pull_season(client, season)
        rprint(f"[green]{season}[/]: {played} games played, {fetched} box scores fetched now")


@app.command("pull-platform")
def pull_platform(
    matchday_id: int = typer.Option(None, help="Fantaking matchday id; default = current"),
    history: bool = typer.Option(False, "--history", help="also pull per-player fantasy-pts for past matchdays"),
):
    """Pull league config, my team, roster and the full player market; append the price log."""
    from elfa.ingest.fantaking import FantakingClient, pull_matchday

    s = Settings.load()
    try:
        out = pull_matchday(FantakingClient(s), matchday_id, with_history=history)
    except Exception as e:  # noqa: BLE001 - never print request objects/headers
        rprint(f"[red]pull-platform failed:[/] {type(e).__name__}: {_redact(str(e), s.fantaking_token)}")
        raise typer.Exit(1)
    tmd = json.loads((out / "team_matchday.json").read_text(encoding="utf-8"))
    rprint(f"[green]pulled[/] -> {out}")
    rprint(f"team: {tmd['name']}  credits: {tmd['credits']}  trades used: {tmd['trades']}/{tmd['max_num_trades_per_matchday']}")


@app.command()
def build(seasons: str = typer.Option("E2026")):
    """Flatten box scores to player_games.parquet and build team/player maps."""
    from elfa.features.boxscores import build_player_games, summary
    from elfa.features.mapping import load_latest_market, map_players, map_teams

    df = build_player_games([s.strip() for s in seasons.split(",")])
    rprint(summary(df))
    _md, market, cfg = load_latest_market()
    games = json.loads((PROCESSED.parent / "raw" / "euroleague" / df.season.max() / "games.json").read_text(encoding="utf-8"))
    tm = map_teams(cfg["teams"], games)
    bad = tm[~tm.method.isin(["seed", "name"])]
    rprint(f"teams mapped: {len(tm)}; needs attention: {len(bad)}")
    if len(bad):
        rprint(bad.to_string(index=False))
    pm = map_players(market, df, tm)
    rprint(pm.method.value_counts().to_string())
    from elfa.features.context import write_context
    from elfa.features.dvp import attach_positions
    from elfa.features.matchdays import write_matchdays
    from elfa.ingest.external import update_price_base
    from elfa.ingest.odds import consensus, latest_snapshot, odds_dir
    from elfa.model.teams import team_ratings

    cur = df[df.season == df.season.max()]
    cur = attach_positions(cur, pm, market)
    snap = latest_snapshot(odds_dir(), max_age_h=24 * 14)
    odds = consensus(snap[0], games) if snap else {}
    ctx, usage, fdr = write_context(cur, games, team_ratings(cur, games), odds, from_round=_md)
    rprint(f"team context: {len(ctx)} clubs · usage: {len(usage)} players · FDR: {fdr.team.nunique() if len(fdr) else 0} clubs x next {int(fdr.n.max()) if len(fdr) else 0}")
    pb = update_price_base(market, _md)
    rprint("price base: " + ", ".join(f"{k} {v}" for k, v in pb.source.value_counts().items()))
    mds = write_matchdays(games, cfg, market, tm)
    cur = mds[mds.deadline_utc.notna()]
    rprint(f"matchdays: {mds.matchday.nunique()} (one per round) · current "
           + (f"MD {int(cur.matchday.iloc[0])} = R{int(cur['round'].iloc[0])}, nights " + ", ".join(f"T{int(r.turn)}={r.date_utc}" for r in cur.itertuples()) if len(cur) else "unknown"))


@app.command("pull-external")
def pull_external():
    """Download the Fantasy Edge IQ player CSV (season-start prices, cross-source check) and update price_base.csv."""
    from elfa.features.mapping import load_latest_market
    from elfa.ingest.external import fetch_fantasyedge, update_price_base

    fetch_fantasyedge()
    md, market, _cfg = load_latest_market()
    pb = update_price_base(market, md)
    rprint("price base: " + ", ".join(f"{k} {v}" for k, v in pb.source.value_counts().items()))


@app.command("probe-trend")
def probe_trend(ids: str = typer.Option("3766,7424,3850", help="comma-separated platform player ids")):
    """Dump raw /trend, /profile and /upcoming-matches responses for a few players (looking for a price series)."""
    from elfa.config import RAW, Settings
    from elfa.ingest.fantaking import FantakingClient

    s = Settings.load()
    c = FantakingClient(s)
    out = RAW / "fantaking" / "probe"
    out.mkdir(parents=True, exist_ok=True)
    for pid in [i.strip() for i in ids.split(",") if i.strip()]:
        for name, path, params in (("trend", f"/api/v1/players/{pid}/trend", {"league": s.league_id}),
                                   ("profile", f"/api/v1/players/{pid}/profile", {"league": s.league_id, "lang": "en"}),
                                   ("upcoming", f"/api/v1/players/{pid}/upcoming-matches", {"league": s.league_id})):
            try:
                data = c.get(path, **params)
            except Exception as e:  # noqa: BLE001 - a probe reports and moves on
                rprint(f"{pid} {name}: {type(e).__name__} {str(e)[:80]}")
                continue
            fp = out / f"{pid}_{name}.json"
            fp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            keys = list(data.get("data", data).keys()) if isinstance(data.get("data", data), dict) else type(data.get("data", data)).__name__
            rprint(f"{pid} {name}: {fp.name} keys={keys}")
    rprint("look for quotation/price arrays in the trend and profile files")


@app.command()
def reconcile():
    """Phase 0 gate: compare platform fantasy points with official PIR per player-game."""
    from elfa.model.reconcile import gate_report
    from elfa.model.reconcile import reconcile as _rec

    rprint(gate_report(_rec()))


@app.command()
def backtest(rounds: str = typer.Option("", help="comma-separated; default = every played round from R4"), grid: bool = typer.Option(False, "--grid")):
    """P1 gate: walk-forward backtest of the projection vs season-mean and last-3 baselines."""
    import pandas as pd

    from elfa.features.dvp import attach_positions
    from elfa.features.mapping import load_latest_market
    from elfa.model.backtest import backtest as _bt
    from elfa.model.backtest import grid_search
    from elfa.model.teams import load_schedule

    pg = pd.read_parquet(PROCESSED / "player_games.parquet")
    pg = pg[pg.season == pg.season.max()]
    _md, market, _cfg = load_latest_market()
    pm = pd.read_csv(PROCESSED / "player_map.csv", dtype={"platform_id": str, "person_code": str})
    pg = attach_positions(pg, pm, market)
    sched = load_schedule(pg.season.max())
    rs = [int(x) for x in rounds.split(",")] if rounds else sorted(int(r) for r in pg.loc[pg.played, "round"].unique() if r >= 4)
    if grid:
        g = grid_search(pg, sched, rs)
        rprint(g.head(10).to_string(index=False))
        g.to_csv(PROCESSED / "backtest_grid.csv", index=False)
        return
    res = _bt(pg, sched, rs)
    rprint(res.summary.to_string(index=False))
    res.table.to_csv(PROCESSED / "backtest_rounds.csv", index=False)


@app.command("pull-top")
def pull_top_cmd(n: int = typer.Option(100), tournament: int = typer.Option(191896, help="Global league id")):
    """Crawl the top-N teams' public rosters for every played matchday (cached; only new files are fetched)."""
    from elfa.features.mapping import load_latest_market
    from elfa.ingest.fantaking import FantakingClient
    from elfa.ingest.top_teams import pull_top

    s = Settings.load()
    md, _market, cfg = load_latest_market()
    played = [m for m in cfg["matchdays"] if m["number"] < md]
    try:
        k = pull_top(FantakingClient(s, sleep=0.3), played, tournament, n)
    except Exception as e:  # noqa: BLE001
        rprint(f"[red]pull-top failed:[/] {type(e).__name__}: {_redact(str(e), s.fantaking_token)}")
        raise typer.Exit(1)
    rprint(f"top-{n}: {k} roster previews fetched now")


@app.command("top-analyse")
def top_analyse():
    """Summarise what the top managers do (ownership, captains, trades, swaps, budget)."""
    from elfa.features.mapping import load_latest_market
    from elfa.features.top_analysis import analyse, load_top_rosters

    _md, market, _cfg = load_latest_market()
    rprint(analyse(load_top_rosters(), market))


@app.command()
def evaluate():
    """Score past projections against actual platform points; write evaluation.md."""
    from elfa.model.evaluate import evaluate as _ev

    _df, txt = _ev()
    rprint(txt)


@app.command()
def scorecard():
    """Decision scorecard per played matchday: team expected vs actual, regret, captain and trade value."""
    from elfa.model.scorecard import scorecard as _sc

    _df, txt = _sc()
    rprint(txt)


@app.command()
def learn():
    """Guarded recalibration: minutes/rate sub-model grids, bias layer, sd calibration, challenger, drift check."""
    import pandas as pd

    from elfa.features.dvp import attach_positions
    from elfa.features.mapping import load_latest_market
    from elfa.model.evaluate import learn as _learn
    from elfa.model.teams import load_schedule

    pg = pd.read_parquet(PROCESSED / "player_games.parquet")
    pg = pg[pg.season == pg.season.max()]
    _md, market, _cfg = load_latest_market()
    pm = pd.read_csv(PROCESSED / "player_map.csv", dtype={"platform_id": str, "person_code": str})
    pg = attach_positions(pg, pm, market)
    rounds = sorted(pg["round"].unique().tolist())
    rounds = [r for r in rounds if r >= 4]
    rprint(_learn(pg, load_schedule(pg.season.max()), rounds))


@app.command()
def recommend(
    mu_price: float = typer.Option(0.0, help="weight of expected price change (PIR per credit)"),
    keep: str = typer.Option("", help="comma-separated player names (substring) that must stay in the squad"),
):
    """Project, optimise and write reports/recommendation_mdXX.md."""
    from elfa.report.recommend import recommend as _rec

    out = _rec(mu_price=mu_price, keep=[k.strip() for k in keep.split(",") if k.strip()])
    rprint(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    app()
