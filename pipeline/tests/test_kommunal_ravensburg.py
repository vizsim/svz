"""Golden-Test Ravensburg (Kommune, Punkte): Übersichts-Excel mit 4 Zählblöcken.

Fixiert: Blöcke -> lange Tabelle, Leerstrings -> NaN, jüngste Zählung je Zählstelle,
Jahr je Feature (year_from), Straßenklasse/-nummer aus dem NAME-Token, level=kommune.
"""

from __future__ import annotations

import pandas as pd

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.adapters.kommunal import ravensburg


def _fake_excel(*_a, **_k) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": [1000, 1005, 1044],
            "NAME": [
                "Eywiesenstraße_Gartenstraße_88212_Ravensburg",
                "B32_Ulmerstraße_88212_Ravensburg",
                "Markdorferstraße_L288_88213_Ravensburg",
            ],
            "BREITENGRAD": [47.79055, 47.794948, 47.774178],
            "LAENGENGRAD": [9.6211755, 9.6150112, 9.569811],
            "KFZ_1": [14217, 30262, "21016"],       # String -> Int
            "RAD_1": [275, 4, 100],
            "FUSSGAENGER_1": [285, 1, 50],
            "SV_1": [1919, 4421, 4684],
            "DATUM_1": ["2023-11-16", "2024-07-11", "2025-01-30"],
            "KFZ_2": [14777, "", ""],               # Leerstring = keine 2. Zählung
            "RAD_2": [737, "", ""],
            "FUSSGAENGER_2": [285, "", ""],
            "SV_2": [2113, "", ""],
            "Datum_4": [None, None, None],          # Klein-/Großschreibung + unvollständiger Block
            "DATUM_2": ["2024-07-11", "", ""],
        }
    )


def test_ravensburg_latest_count_per_station(monkeypatch) -> None:
    monkeypatch.setattr(base, "read_excel_zip", _fake_excel)
    gdf = ravensburg.normalize().sort_values("station_id").reset_index(drop=True)

    schema.validate(gdf, where="ravensburg")
    assert set(gdf.geom_type) == {"Point"}
    assert len(gdf) == 3                                      # eine Zeile je Zählstelle
    assert set(gdf["level"]) == {"kommune"} and set(gdf["state"]) == {"BW"}
    assert set(gdf["metric"]) == {"24h"}                      # Einzelzählung, kein DTV
    assert list(gdf["station_id"]) == ["1000", "1005", "1044"]
    # 1000: jüngste Zählung (2024-07-11) gewinnt gegen die erste (2023).
    assert list(gdf["dtv_kfz"]) == [14777, 30262, 21016]
    assert list(gdf["year"]) == [2024, 2024, 2025]            # Jahr je Feature
    assert list(gdf["road_class"]) == ["G", "B", "L"]
    assert pd.isna(gdf.loc[0, "road_no"]) and list(gdf["road_no"][1:]) == ["B 32", "L 288"]
    assert gdf.loc[0, "name"] == "Eywiesenstraße / Gartenstraße"   # ohne PLZ/Ort
    assert gdf.loc[1, "name"] == "B 32 / Ulmerstraße"
