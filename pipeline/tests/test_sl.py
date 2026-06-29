"""Golden-Test SL (Punkte): ArcGIS-WFS-Zählstellen -> kanonisches Schema."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point

from svzkarte import schema
from svzkarte.adapters import base, sl


def _fake_wfs(*_a, **_k) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "Str": ["L 375", "B268", "A8", "K 12"],   # road_class aus Präfix
            "TKZST": ["65050739", "1", "2", "3"],
            "DTV": ["1692", "9000", "48000", "800"],
            "DTVSV": ["67", "400", "5200", "30"],
            "geometry": [Point(6.64, 49.50), Point(6.9, 49.3), Point(7.0, 49.2), Point(6.8, 49.4)],
        },
        crs="EPSG:4326",
    )


def test_sl_points_normalize(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    gdf = sl.normalize()

    schema.validate(gdf, where="sl")
    assert set(gdf.geom_type) == {"Point"}
    assert set(gdf["state"]) == {"SL"} and set(gdf["metric"]) == {"DTV"}
    assert list(gdf["road_class"]) == ["L", "B", "A", "K"]   # aus Str-Präfix
    assert list(gdf["road_no"]) == ["L 375", "B268", "A8", "K 12"]
    assert list(gdf["dtv_kfz"]) == [1692, 9000, 48000, 800]
