"""Golden-Test BW (Punkte): CSV-Zählstellen -> kanonisches Schema."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point

from svzkarte import schema
from svzkarte.adapters import base, bw


def _fake_csv_points(*_a, **_k) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "klasse": ["L", "B", "A"],
            "nummer": ["508", "27", "81"],
            "svznr": ["62221200", "1", "2"],
            "DTV2024": ["6626", "24000", "0"],     # String -> Int
            "DTVSV": ["253", "1800", "0"],
            "geometry": [Point(9.47, 49.74), Point(9.1, 48.8), Point(9.9, 48.5)],
        },
        crs="EPSG:4326",
    )


def test_bw_points_normalize(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_csv_points", _fake_csv_points)
    gdf = bw.normalize()

    schema.validate(gdf, where="bw")
    assert set(gdf.geom_type) == {"Point"}
    assert set(gdf["state"]) == {"BW"} and set(gdf["year"]) == {2024}
    assert list(gdf["road_class"]) == ["L", "B", "A"]
    assert list(gdf["road_no"]) == ["L 508", "B 27", "A 81"]
    assert list(gdf["dtv_kfz"][:2]) == [6626, 24000]
    assert gdf["dtv_kfz"].isna().tolist() == [False, False, True]   # "0" = nicht gezählt (#2)
    assert gdf["dtv_sv"].isna().tolist() == [False, False, True]
