"""Merge: alle data/interim/<land>.fgb -> nach Geometrietyp getrennt (validiert).

Linien-Länder (Zählstellenbereiche/Segmente) und Punkt-Länder (Zählstellen-
Standorte, z.B. BW/SL) landen in getrennten FGB — FlatGeobuf hält nur einen
Geometrietyp, und im Frontend rendern Linien- und Punkt-Layer separat. tiles.py
fügt beide per tile-join zu einem svz_de.pmtiles (Layer `svz` + `svz_points`).
"""

from __future__ import annotations

from pathlib import Path

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.config import get_paths

OUT = {"lines": "svz_lines.fgb", "points": "svz_points.fgb"}


def _kind(gdf) -> str:
    return "points" if set(gdf.geom_type) <= {"Point", "MultiPoint"} else "lines"


def merge() -> dict[str, Path]:
    import geopandas as gpd
    import pandas as pd

    paths = get_paths()
    parts = sorted(paths.interim.glob("*.fgb"))
    if not parts:
        raise FileNotFoundError(f"Keine Länder-FGB in {paths.interim} — erst `svz build all`.")

    groups: dict[str, list] = {"lines": [], "points": []}
    for p in parts:
        g = gpd.read_file(p)
        groups[_kind(g)].append(g)

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
