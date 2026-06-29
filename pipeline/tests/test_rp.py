"""Golden-Test RP: normalize() mappt WFS-Felder korrekt aufs kanonische Schema.

Ohne Netz: base.fetch_wfs wird durch ein synthetisches GeoDataFrame ersetzt, das
die dokumentierten Quell-Spalten (DTV/DTV_SV/strasse/klasse, UTM32N) trägt. So ist
das Adapter-Mapping fixiert, auch solange der Live-Dienst (393) down ist.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base, rp


def _fake_wfs(*_args, **_kwargs) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "DTV": [12000, 5400],
            "DTV_SV": [900, 210],
            "strasse": ["B10", "L1187"],
            "zst_nr": ["5012", "5099"],
            "klasse": ["B", "L"],
            "geometry": [
                LineString([(400000, 5500000), (400120, 5500000)]),
                LineString([(400000, 5500100), (400200, 5500100)]),
            ],
        },
        crs="EPSG:25832",
    )


def test_rp_normalize_maps_to_canonical(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    gdf = rp.normalize()

    schema.validate(gdf, where="rp")
    assert gdf.crs.to_epsg() == schema.EPSG
    assert set(gdf["state"]) == {"RP"} and set(gdf["metric"]) == {"DTV"}
    assert set(gdf["road_class"]) == {"B", "L"}
    assert list(gdf["road_no"]) == ["B10", "L1187"]
    assert list(gdf["dtv_kfz"]) == [12000, 5400]
    assert set(gdf["year"]) == {2021}
