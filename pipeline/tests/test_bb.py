"""Golden-Test Brandenburg: normalize() mappt den Verkehrsstärke-WFS aufs Schema.

Ohne Netz: base.fetch_wfs liefert ein synthetisches GeoDataFrame mit den echten
GML-Spalten (KFZ als STRING wie "1281.0", EPSG:25833). Fixiert Mapping, die
String->Int-Coercion (BB-GML-Falle) und die Reprojektion 25833 -> 4326.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

from svzkarte import schema
from svzkarte.adapters import base, bb


def _fake_wfs(*_a, **_k) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "klasse": ["L", "B", "A", "K"],
            "strasse": ["L711", "B 1", "A 10", "K 6803"],
            "zaehlstellennummer": ["40473001", "1", "2", "3"],
            "KFZ": ["1281.0", "12000.0", "93708.0", None],   # String + None
            "DTV_SV": ["79.0", "900.0", "15800.0", "5.0"],
            "SV_KFZ": ["6.2", "7.5", "16.9", "8.0"],
            "jahr": ["2021.0"] * 4,                          # Fremdspalte -> verworfen
            "geometry": [
                MultiLineString([[(360000, 5800000), (360200, 5800000)]]),
                LineString([(370000, 5810000), (370300, 5810000)]),
                LineString([(380000, 5820000), (380100, 5820000)]),
                LineString([(390000, 5830000), (390100, 5830000)]),
            ],
        },
        crs="EPSG:25833",
    )


def test_bb_normalize_coerces_strings_and_reprojects(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    gdf = bb.normalize()

    schema.validate(gdf, where="bb")
    assert gdf.crs.to_epsg() == schema.EPSG               # 25833 -> 4326
    assert set(gdf["state"]) == {"BB"} and set(gdf["metric"]) == {"DTV"}
    assert list(gdf["road_class"]) == ["L", "B", "A", "K"]
    assert list(gdf["road_no"]) == ["L711", "B 1", "A 10", "K 6803"]
    assert list(gdf["dtv_kfz"].dropna()) == [1281, 12000, 93708]  # String -> Int
    assert gdf["dtv_kfz"].isna().sum() == 1                       # None -> <NA>
    assert str(gdf["dtv_kfz"].dtype) == "Int64"
    assert "jahr" not in gdf.columns
