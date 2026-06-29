"""Merge: alle data/interim/<land>.fgb -> data/svz/svz_de.fgb (kanonisch, validiert).

Ein einziges Tile-Set entsteht später aus dieser einen FGB; gefiltert wird im
Frontend über state/year/metric/road_class. Vor dem Schreiben läuft `schema.validate`
über das Gesamt-Ergebnis — eine kaputte Länder-FGB fällt hier auf.
"""

from __future__ import annotations

from pathlib import Path

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.config import get_paths

_OUT = "svz_de.fgb"


def merge() -> tuple[Path, int]:
    import geopandas as gpd
    import pandas as pd

    paths = get_paths()
    parts = sorted(paths.interim.glob("*.fgb"))
    if not parts:
        raise FileNotFoundError(f"Keine Länder-FGB in {paths.interim} — erst `svz build all`.")

    frames = [gpd.read_file(p) for p in parts]
    merged = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True), geometry="geometry", crs=f"EPSG:{schema.EPSG}"
    )
    schema.validate(merged, where="merge")

    out, n = base.write_fgb(merged, paths.svz / _OUT)
    print(f"  {len(parts)} Länder, {n} Features -> {out}")
    return out, n
