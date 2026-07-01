"""Merge: alle data/interim/<land>.fgb -> nach Datensatz/Geometrie getrennt (validiert).

Drei Ausgaben, weil FlatGeobuf nur einen Geometrietyp hält und BASt ein eigenes,
im Frontend separat schaltbares PMTiles bekommt:
  - svz_lines.fgb   Länder-Linien (Zählstellenbereiche/Segmente)   -> Layer `svz`
  - svz_points.fgb  Länder-Punkte (Zählstellen-Standorte, BW/SL)   -> Layer `svz_points`
  - svz_bast.fgb    BASt-Backbone (Bundesfernstraßen A+B, Punkte)  -> eigenes svz_bast.pmtiles
"""

from __future__ import annotations

from pathlib import Path

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.config import get_paths

OUT = {"lines": "svz_lines.fgb", "points": "svz_points.fgb", "bast": "svz_bast.fgb"}


def _group(gdf) -> str:
    if "source" in gdf.columns and (gdf["source"] == "bast").all():
        return "bast"  # BASt in eigenes PMTiles, unabhängig vom Geometrietyp
    return "points" if set(gdf.geom_type) <= {"Point", "MultiPoint"} else "lines"


def merge() -> dict[str, Path]:
    import geopandas as gpd
    import pandas as pd

    paths = get_paths()
    parts = sorted(paths.interim.glob("*.fgb"))
    if not parts:
        raise FileNotFoundError(f"Keine Länder-FGB in {paths.interim} — erst `svz build all`.")

    groups: dict[str, list] = {"lines": [], "points": [], "bast": []}
    for p in parts:
        g = gpd.read_file(p)
        groups[_group(g)].append(g)

    written: dict[str, Path] = {}
    for kind, frames in groups.items():
        if not frames:
            continue
        merged = gpd.GeoDataFrame(
            pd.concat(frames, ignore_index=True), geometry="geometry", crs=f"EPSG:{schema.EPSG}"
        )
        schema.validate(merged, where=f"merge/{kind}")
        out, n = base.write_fgb(merged, paths.svz / OUT[kind])
        print(f"  {kind}: {len(frames)} Länder, {n} Features -> {out}")
        written[kind] = out
    return written
