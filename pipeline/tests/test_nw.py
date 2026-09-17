"""Golden-Test NRW: normalize() mappt das Verkehrswerte-Shapefile aufs Schema.

Ohne Netz: base.fetch_zip liefert ein synthetisches GeoDataFrame mit den echten
Shapefile-Spalten (DTVKFZA/DTVSVA/STRKL/STRBEZ/ZSTNR, EPSG:25832). Fixiert die
Auswahl der A-Variante (alle Tage) und die Reprojektion 25832 -> 4326.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base, nw


def _fake_zip(*_a, **_k) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "STRKL": ["L", "B", "K"],
            "STRBEZ": ["L593", "B54", "K1"],
            "STRNR": ["593", "54", "1"],            # Fremdspalte -> verworfen
            "ZSTNR": ["35111302", "1", "2"],
            "DTVKFZA": [851.0, 24000.0, 0.0],       # A = alle Tage -> dtv_kfz
            "DTVKFZW": [785.0, 25000.0, 0.0],       # W = Werktage -> NICHT genommen
            "DTVSVA": [86.0, 1800.0, 5.0],
            "geometry": [
                LineString([(400000, 5700000), (400200, 5700000)]),
                LineString([(410000, 5710000), (410300, 5710000)]),
                LineString([(420000, 5720000), (420100, 5720000)]),
            ],
        },
        crs="EPSG:25832",
    )


def test_nw_normalize_picks_alltage_and_reprojects(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_zip", _fake_zip)
    gdf = nw.normalize()

    schema.validate(gdf, where="nw")
    assert gdf.crs.to_epsg() == schema.EPSG               # 25832 -> 4326
    assert set(gdf["state"]) == {"NW"} and set(gdf["metric"]) == {"DTV"}
    assert set(gdf["year"]) == {2019}
    assert list(gdf["road_class"]) == ["L", "B", "K"]
    assert list(gdf["road_no"]) == ["L593", "B54", "K1"]
    assert list(gdf["dtv_kfz"][:2]) == [851, 24000]       # A-Variante, nicht W
    assert gdf["dtv_kfz"].isna().tolist() == [False, False, True]   # 0 = nicht gezählt (#2)
    assert "STRNR" not in gdf.columns
