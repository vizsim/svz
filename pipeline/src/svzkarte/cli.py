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
    for level in ("bund", "land", "kommune"):
        typer.echo(f"live/{level:<8} {', '.join(registry.by_level(level)) or '—'}")
    typer.echo(f"offen:         {', '.join(registry.PLANNED) or '—'}")
    try:
        n = len(load_yaml("sources.yaml").get("sources", {}))
        typer.echo(f"sources.yaml:  {n} Quellen-Einträge")
    except FileNotFoundError:
        typer.secho("sources.yaml fehlt", fg=typer.colors.RED)


@app.command()
def build(
    land: str = typer.Argument(..., help="Quellen-Code (z.B. by, bast, ravensburg) oder 'all'"),
) -> None:
    """fetch+normalize -> data/interim/<quelle>.fgb (validiert)."""
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
    """interim/*.fgb -> data/svz/ je Ebene × Geometrie (Länder/BASt/Kommunen, validiert)."""
    from svzkarte import merge as merge_mod

    written = merge_mod.merge()
    for kind, path in written.items():
        typer.secho(f"geschrieben: {kind} -> {path}", fg=typer.colors.GREEN)


@app.command()
def tiles(
    dry_run: bool = typer.Option(False, "--dry-run", help="Kommandos nur zeigen"),
    only: str = typer.Option(
        "", "--only", help="nur diese Datensätze (Komma): svz_de, svz_bast, svz_kommunal"
    ),
) -> None:
    """svz_de.pmtiles (Länder) + svz_bast.pmtiles (Bund) + svz_kommunal.pmtiles (Kommunen)."""
    from svzkarte import tiles as tiles_mod

    wanted = {s.strip() for s in only.split(",") if s.strip()} or None
    for name, path in tiles_mod.build_svz(dry_run=dry_run, only=wanted).items():
        typer.secho(f"PMTiles {name}: {path}", fg=typer.colors.GREEN)


@app.command()
def manifest() -> None:
    """Generiert data/manifest.json (Datenstand/Attribution je Quelle)."""
    from svzkarte import manifest as manifest_mod

    out = manifest_mod.generate()
    typer.secho(f"geschrieben: {out}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
