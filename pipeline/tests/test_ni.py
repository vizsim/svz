"""Golden-Test Niedersachsen: normalize() mappt das Shapefile aufs kanonische Schema.

Ohne Netz: base.fetch_zip wird ersetzt und liefert ein synthetisches GeoDataFrame
mit den echten Shapefile-Spalten (dtv21/dtvsv21/strkl/strbez/zstnr, EPSG:25832).
Fixiert Mapping, Reprojektion (UTM32N -> 4326) und strkl-Default.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

from svzkarte import schema
from svzkarte.adapters import base, ni


def _fake_zip(*_a, **_k) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "strkl": ["A", "B", "L", "X"],          # X ist kein Enum -> Fallback L
            "strbez": ["A 1", "B 6", "L 410", "L 9"],
            "zstnr": ["25263351", "31100012", "40020003", "40020004"],
            "dtv21": [99994.0, 12000.0, 3400.0, 800.0],
            "dtvsv21": [15845.0, 900.0, 210.0, 40.0],
            "Shape_Leng": [6070.3, 1200.0, 800.0, 300.0],  # Fremdspalte -> verworfen
            "geometry": [
                LineString([(550000, 5800000), (550200, 5800000)]),
                MultiLineString([[(560000, 5810000), (560300, 5810000)]]),
                LineString([(570000, 5820000), (570100, 5820000)]),
                LineString([(580000, 5830000), (580100, 5830000)]),
            ],
        },
        crs="EPSG:25832",
    )


def test_ni_normalize_maps_and_reprojects(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_zip", _fake_zip)
    gdf = ni.normalize()

    schema.validate(gdf, where="ni")
    assert gdf.crs.to_epsg() == schema.EPSG               # 25832 -> 4326
    assert set(gdf["state"]) == {"NI"} and set(gdf["metric"]) == {"DTV"}
    assert set(gdf["year"]) == {2021}
    assert list(gdf["road_class"]) == ["A", "B", "L", "L"]  # X -> Fallback L
    assert list(gdf["road_no"]) == ["A 1", "B 6", "L 410", "L 9"]
    assert list(gdf["dtv_kfz"]) == [99994, 12000, 3400, 800]
    assert list(gdf["dtv_sv"]) == [15845, 900, 210, 40]
    assert "Shape_Leng" not in gdf.columns
