"""Golden-Test Sachsen-Anhalt: Netz-WFS (Geometrie) × Excel-DTV über Netzknoten.

Ohne Netz: base.fetch_wfs liefert die Netzsegmente (vnk/nnk, EPSG:25832),
base.read_excel_zip die DTV-Tabelle (VonNK/NachNK, DTV als String). Fixiert den
Join (vnk,nnk)<->(VonNK,NachNK), die String->Int-Coercion und die Reprojektion.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base, st


def _fake_wfs(_url: str, _typename: str, **_k) -> gpd.GeoDataFrame:
    # Wird je Klasse aufgerufen; gleiche Segmente -> drop_duplicates dedupt.
    return gpd.GeoDataFrame(
        {
            "vnk": ["100", "300", "500"],
            "nnk": ["200", "400", "600"],
            "geometry": [
                LineString([(640000, 5700000), (640300, 5700000)]),
                LineString([(650000, 5710000), (650300, 5710000)]),
                LineString([(660000, 5720000), (660300, 5720000)]),
            ],
        },
        crs="EPSG:25832",
    )


def _fake_excel(*_a, **_k) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "VonNK": [100, 300, 999],          # 999 ohne Netz-Match -> fällt weg
            "NachNK": [200, 400, 888],
            "Str": ["A 2", "B 246", "L 50"],
            "TKZST": ["37383810", "1", "2"],
            "DTV": ["49384", "12000", "3400"],   # String -> Int
            "DTVSV": ["14701", "900", "210"],
        }
    )


def test_st_join_net_and_excel(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    monkeypatch.setattr(base, "read_excel_zip", _fake_excel)
    gdf = st.normalize().sort_values("station_id").reset_index(drop=True)

    schema.validate(gdf, where="st")
    assert gdf.crs.to_epsg() == schema.EPSG               # 25832 -> 4326
    assert len(gdf) == 2                                   # nur (100,200) & (300,400) matchen
    assert set(gdf["state"]) == {"ST"} and set(gdf["year"]) == {2021}
    assert sorted(gdf["road_class"]) == ["A", "B"]
    assert sorted(gdf["dtv_kfz"]) == [12000, 49384]       # gejoint + coerct
    assert set(gdf.geom_type) == {"LineString"}
