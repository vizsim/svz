"""Tests für merge: Gruppierung Ebene × Geometrie + Nachrüsten älterer interim-FGB."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString, Point

from svzkarte import merge, schema
from svzkarte.adapters import base


def _gdf(level: str, source: str, geom) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"source": [source], "level": [level], "geometry": [geom]}, crs="EPSG:4326"
    )


def test_group_by_level_and_geometry() -> None:
    line, pt = LineString([(9, 47), (9.1, 47)]), Point(9, 47)
    assert merge._group(_gdf("land", "by", line)) == "lines"
    assert merge._group(_gdf("land", "bw", pt)) == "points"
    assert merge._group(_gdf("bund", "bast", pt)) == "bast"
    assert merge._group(_gdf("kommune", "koeln", line)) == "kommunal_lines"
    assert merge._group(_gdf("kommune", "ravensburg", pt)) == "kommunal_points"


def test_backfill_old_interim_without_level_and_name() -> None:
    # interim-FGB aus der Zeit vor `level`/`name`: Ebene aus sources.yaml, name leer.
    old = gpd.GeoDataFrame({"source": ["bast"], "geometry": [Point(9, 47)]}, crs="EPSG:4326")
    out = merge._backfill(old)
    assert list(out["level"]) == ["bund"] and out["name"].isna().all()


def test_source_level_from_sources_yaml() -> None:
    assert base.source_level("ravensburg") == "kommune"
    assert base.source_level("by") == "land"
    assert base.source_level("bast") == "bund"
    assert set(schema.LEVELS) == {"bund", "land", "kommune"}
