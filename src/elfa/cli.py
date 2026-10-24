"""elfa command-line entry point.

Phase 0 skeleton — commands are stubs until ingest lands.
"""
import typer

app = typer.Typer(help="EuroLeague Fantasy Agent")


@app.command()
def pull(matchday: int = typer.Option(None, help="Fantaking matchday id; default = current")):
    """Pull platform market + roster and official box scores into data/raw."""
    typer.echo("TODO: ingest")


@app.command()
def recommend(horizon: int = 3):
    """Project, optimise and print the recommended lineup and trades."""
    typer.echo("TODO: recommend")


if __name__ == "__main__":
    app()
