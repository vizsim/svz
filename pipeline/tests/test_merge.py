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
    old = gpd.GeoDataFrame(
        {"source": ["bast"], "dtv_kfz": [41000], "dtv_sv": [5200], "geometry": [Point(9, 47)]},
        crs="EPSG:4326",
    )
    out = merge._backfill(old)
    assert list(out["level"]) == ["bund"] and out["name"].isna().all()


def test_backfill_old_interim_zero_placeholders() -> None:
    # Issue #2: interim-FGB von vor dem Fix tragen 0 für „nicht gezählt" (float, wie pyogrio
    # Integer-Spalten mit Nulls liest) -> beim Merge leer, ohne die Quelle neu zu bauen.
    old = gpd.GeoDataFrame(
        {
            "source": ["bw"] * 3, "level": ["land"] * 3, "name": [None] * 3,
            "dtv_kfz": [0.0, 6626.0, float("nan")], "dtv_sv": [0.0, 0.0, 12.0],
            "geometry": [Point(9, 47), Point(9.1, 47), Point(9.2, 47)],
        },
        crs="EPSG:4326",
    )
    out = merge._backfill(old)
    assert out["dtv_kfz"].isna().tolist() == [True, False, True]
    assert out["dtv_sv"].isna().tolist() == [True, False, False]
    assert out["dtv_kfz"].dtype == "Int64" and out["dtv_sv"].iloc[1] == 0


def test_source_level_from_sources_yaml() -> None:
    assert base.source_level("ravensburg") == "kommune"
    assert base.source_level("by") == "land"
    assert base.source_level("bast") == "bund"
    assert set(schema.LEVELS) == {"bund", "land", "kommune"}
