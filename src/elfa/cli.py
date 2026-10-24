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


@app.command()
def reconcile():
    """Phase 0 gate: compare platform fantasy points with official PIR per player-game."""
    from elfa.model.reconcile import gate_report
    from elfa.model.reconcile import reconcile as _rec

    rprint(gate_report(_rec()))


@app.command()
def recommend(horizon: int = 3):
    """Project, optimise and print the recommended lineup and trades (Phase 1)."""
    rprint("[yellow]not implemented yet - Phase 1[/]")


if __name__ == "__main__":
    app()
