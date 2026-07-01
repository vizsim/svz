"""CLI-Einstieg: `svz <befehl>`.

Datenfluss je Land: fetch -> normalize -> data/interim/<land>.fgb (`build`),
dann einmal `merge` -> data/svz/svz_de.fgb, dann `tiles` -> svz_de.pmtiles.
Ein einziges Tile-Set; gefiltert wird im Frontend (state/year/metric/road_class).
cli bleibt dünn: lazy import + Aufruf (Muster aus `unfallkarte`).
"""

from __future__ import annotations

import typer

from svzkarte import __version__
from svzkarte.config import get_paths, load_yaml

app = typer.Typer(no_args_is_help=True, add_completion=False, help="svzkarte Pipeline")


@app.command()
def info() -> None:
    """Zeigt aufgelöste Pfade/Config + Adapter-Status (Smoke-Check)."""
    from svzkarte import registry

    paths = get_paths()
    typer.echo(f"svzkarte {__version__}")
    typer.echo(f"root:     {paths.root}")
    typer.echo(f"data:     {paths.data}")
    typer.echo(f"implementiert: {', '.join(registry.REGISTRY) or '—'}")
    typer.echo(f"geplant:       {', '.join(registry.PLANNED) or '—'}")
    try:
        n = len(load_yaml("sources.yaml").get("sources", {}))
        typer.echo(f"sources.yaml:  {n} Land-Einträge")
    except FileNotFoundError:
        typer.secho("sources.yaml fehlt", fg=typer.colors.RED)


@app.command()
def build(
    land: str = typer.Argument(..., help="Land-Code (z.B. rp) oder 'all'"),
) -> None:
    """fetch+normalize -> data/interim/<land>.fgb (validiert)."""
    from svzkarte import build as build_mod

    if land == "all":
        results = build_mod.build_all()
        ok = [r for r in results if r.error is None]
        bad = [r for r in results if r.error]
        typer.secho(f"OK: {', '.join(r.code for r in ok) or '—'}", fg=typer.colors.GREEN)
        if bad:
            typer.secho(f"Lücken: {', '.join(r.code for r in bad)}", fg=typer.colors.YELLOW)
    else:
        res = build_mod.build_land(land)
        typer.secho(f"{res.code}: {res.n} Features -> {res.fgb}", fg=typer.colors.GREEN)


@app.command()
def merge() -> None:
    """interim/<land>.fgb -> data/svz/svz_lines.fgb + svz_points.fgb (nach Geometrie, validiert)."""
    from svzkarte import merge as merge_mod

    written = merge_mod.merge()
    for kind, path in written.items():
        typer.secho(f"geschrieben: {kind} -> {path}", fg=typer.colors.GREEN)


@app.command()
def tiles(
    dry_run: bool = typer.Option(False, "--dry-run", help="Kommandos nur zeigen"),
) -> None:
    """svz_de.pmtiles (Länder: `svz` + `svz_points`) + svz_bast.pmtiles (Backbone: `bast`)."""
    from svzkarte import tiles as tiles_mod

    for name, path in tiles_mod.build_svz(dry_run=dry_run).items():
        typer.secho(f"PMTiles {name}: {path}", fg=typer.colors.GREEN)


@app.command()
def manifest() -> None:
    """Generiert data/manifest.json (Datenstand/Attribution je Quelle)."""
    from svzkarte import manifest as manifest_mod

    out = manifest_mod.generate()
    typer.secho(f"geschrieben: {out}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
