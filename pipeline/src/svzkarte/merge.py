"""Merge: alle data/interim/<quelle>.fgb -> nach Ebene × Geometrie getrennt (validiert).

FlatGeobuf hält nur einen Geometrietyp, und jede Ebene bekommt ihr eigenes, im
Frontend separat schaltbares PMTiles — daher fünf mögliche Ausgaben:
  Länder   (level=land)     svz_lines.fgb / svz_points.fgb          -> svz_de.pmtiles
  Bund     (level=bund)     svz_bast.fgb   (BASt-Backbone, Punkte)  -> svz_bast.pmtiles
  Kommunen (level=kommune)  kommunal_lines.fgb / kommunal_points.fgb -> svz_kommunal.pmtiles

Ältere interim-FGB (vor `level`/`name`) werden beim Lesen nachgerüstet — `level` aus
sources.yaml, `name` leer — damit kein voller Rebuild aller Länder nötig ist.
"""

from __future__ import annotations

from pathlib import Path

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.config import get_paths

OUT = {
    "lines": "svz_lines.fgb",
    "points": "svz_points.fgb",
    "bast": "svz_bast.fgb",
    "kommunal_lines": "kommunal_lines.fgb",
    "kommunal_points": "kommunal_points.fgb",
}
# Ebene -> Gruppen-Präfix (Bund bleibt der Sonderfall `bast`, nur Punkte).
_PREFIX = {"land": "", "kommune": "kommunal_"}


def _backfill(gdf):
    """Fehlende Schema-Spalten älterer Builds ergänzen (level aus sources.yaml, name=None)."""
    if "level" not in gdf.columns:
        gdf["level"] = base.source_level(str(gdf["source"].iloc[0]))
    if "name" not in gdf.columns:
        gdf["name"] = None
    return gdf


def _group(gdf) -> str:
    """Ziel-Gruppe eines Datensatzes: Ebene (level) × Geometrietyp."""
    is_points = set(gdf.geom_type) <= {"Point", "MultiPoint"}
    level = str(gdf["level"].iloc[0])
    if level == "bund":
        return "bast"  # BASt in eigenes PMTiles, unabhängig vom Geometrietyp
    return _PREFIX[level] + ("points" if is_points else "lines")


def merge() -> dict[str, Path]:
    import geopandas as gpd
    import pandas as pd

    paths = get_paths()
    parts = sorted(paths.interim.glob("*.fgb"))
    if not parts:
        raise FileNotFoundError(f"Keine Quellen-FGB in {paths.interim} — erst `svz build all`.")

    groups: dict[str, list] = {k: [] for k in OUT}
    for p in parts:
        g = gpd.read_file(p)
        if g.empty:
            print(f"  {p.name}: leer, übersprungen")
            continue
        groups[_group(_backfill(g))].append(g)

    written: dict[str, Path] = {}
    for kind, frames in groups.items():
        if not frames:
            continue
        merged = gpd.GeoDataFrame(
            pd.concat(frames, ignore_index=True), geometry="geometry", crs=f"EPSG:{schema.EPSG}"
        )
        merged = merged[[*schema.COLUMNS, "geometry"]]  # feste Spaltenreihenfolge
        schema.validate(merged, where=f"merge/{kind}")
        out, n = base.write_fgb(merged, paths.svz / OUT[kind])
        print(f"  {kind}: {len(frames)} Quellen, {n} Features -> {out}")
        written[kind] = out
    return written
