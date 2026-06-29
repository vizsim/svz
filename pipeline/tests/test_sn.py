"""Golden-Test Sachsen: SVZ-Shapefile -> kanonisches Schema (klasse S -> L)."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base, sn


def _fake_zip(*_a, **_k) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "klasse": ["A", "B", "S", "K"],          # S = Staatsstraße -> L
            "strasse": ["A 13", "B 6", "S 177", "K 1"],
            "nummer": ["46481002", "1", "2", "3"],
            "dtv_kfzges": ["29548.0", "12000.0", "3400.0", None],   # String + None
            "dtv_sv": ["5281.0", "900.0", "210.0", "5.0"],
            "sv_kfz": ["17.9", "7.5", "6.2", "8.0"],
            "bemerkung": ["nan", "nan", "nan", "nan"],   # Fremdspalte -> verworfen
            "geometry": [
                LineString([(300000, 5650000), (300300, 5650000)]),
                LineString([(310000, 5660000), (310300, 5660000)]),
                LineString([(320000, 5670000), (320100, 5670000)]),
                LineString([(330000, 5680000), (330100, 5680000)]),
            ],
        },
        crs="EPSG:25833",
    )


def test_sn_normalize_maps_and_reprojects(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_zip", _fake_zip)
    gdf = sn.normalize()

    schema.validate(gdf, where="sn")
    assert gdf.crs.to_epsg() == schema.EPSG               # 25833 -> 4326
    assert set(gdf["state"]) == {"SN"} and set(gdf["year"]) == {2021}
    assert list(gdf["road_class"]) == ["A", "B", "L", "K"]  # S -> L
    assert list(gdf["road_no"]) == ["A 13", "B 6", "S 177", "K 1"]
    assert list(gdf["dtv_kfz"].dropna()) == [29548, 12000, 3400]
    assert gdf["dtv_kfz"].isna().sum() == 1                  # None -> <NA>
    assert "bemerkung" not in gdf.columns
