"""Golden-Test Hamburg: normalize() fügt HVS+BAB-Layer zusammen und mappt aufs Schema.

Ohne Netz: base.fetch_wfs liefert je typename die HVS- bzw. BAB-Schicht (Felder wie
der echte geodienste.hamburg.de-WFS). Fixiert den Concat, sv -> sv_anteil (Anteil %,
NICHT dtv_sv) und die Klassen-Näherung HVS -> B / BAB -> A.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base, hh


def _fake_wfs(_url: str, typename: str, **_k) -> gpd.GeoDataFrame:
    if "hvs" in typename:
        return gpd.GeoDataFrame(
            {
                "id": [1, 2],
                "dtv": [4000, 33000],
                "sv": [10, 3],                       # Anteil in %
                "strassenklasse": ["HVS", "HVS"],
                "geometry": [
                    LineString([(9.95, 53.61), (9.96, 53.61)]),
                    LineString([(10.0, 53.55), (10.01, 53.55)]),
                ],
            },
            crs="EPSG:4326",
        )
    return gpd.GeoDataFrame(
        {
            "id": [3],
            "dtv": [89000],
            "sv": [12],
            "strassenklasse": ["BAB"],
            "geometry": [LineString([(10.1, 53.5), (10.12, 53.5)])],
        },
        crs="EPSG:4326",
    )


def test_hh_normalize_merges_layers_and_maps(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    gdf = hh.normalize()

    schema.validate(gdf, where="hh")
    assert len(gdf) == 3                                   # HVS (2) + BAB (1)
    assert set(gdf["state"]) == {"HH"} and set(gdf["metric"]) == {"DTV"}
    assert set(gdf["year"]) == {2019}
    assert sorted(gdf["road_class"]) == ["A", "B", "B"]    # BAB->A, HVS->B
    assert list(gdf["sv_anteil"]) == [10, 3, 12]           # Anteil durchgereicht
    assert gdf["dtv_sv"].isna().all()                      # kein absoluter SV in der Quelle
    assert list(gdf["dtv_kfz"]) == [4000, 33000, 89000]
