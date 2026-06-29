"""Golden-Test Bayern: normalize() mappt den BAYSIS-WFS aufs kanonische Schema.

Ohne Netz: base.fetch_wfs wird ersetzt und liefert ein synthetisches GeoDataFrame
mit den echten (umlaut-behafteten) Quell-Spalten, EPSG:4326. Fixiert das Mapping
inkl. Straßenklasse St -> L (Staatsstraße).
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

from svzkarte import schema
from svzkarte.adapters import base, by


def _fake_wfs(*_a, **_k) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "Straßenklasse": ["B", "St", "K", "A"],     # St -> L
            "Straße": ["B 285", "St 2294", "K 1", "A 9"],
            "Zählstelle": ["54269100", "1", "2", "3"],
            "DTV_Kfz": [932.0, 4200.0, 800.0, 134264.0],
            "DTV_SV": [44.0, 210.0, 30.0, 15800.0],
            "Link": ["x", "y", "z", "w"],                # Fremdspalte -> verworfen
            "geometry": [
                MultiLineString([[(10.1, 50.5), (10.2, 50.5)]]),
                LineString([(11.0, 49.0), (11.1, 49.0)]),
                LineString([(12.0, 48.5), (12.1, 48.5)]),
                LineString([(11.5, 48.0), (11.6, 48.0)]),
            ],
        },
        crs="EPSG:4326",
    )


def test_by_normalize_maps_class_and_drops_foreign(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    gdf = by.normalize()

    schema.validate(gdf, where="by")
    assert set(gdf["state"]) == {"BY"} and set(gdf["metric"]) == {"DTV"}
    assert set(gdf["year"]) == {2021}
    assert list(gdf["road_class"]) == ["B", "L", "K", "A"]   # St -> L
    assert list(gdf["road_no"]) == ["B 285", "St 2294", "K 1", "A 9"]
    assert list(gdf["dtv_kfz"]) == [932, 4200, 800, 134264]
    assert "Link" not in gdf.columns
