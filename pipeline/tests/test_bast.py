"""Golden-Test BASt-Backbone: Excel mit X/Y (UTM32N) -> kanonische Punkte."""

from __future__ import annotations

import pandas as pd

from svzkarte import schema
from svzkarte.adapters import base, bast


def _fake_excel(*_a, **_k) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Str": ["A 1", "A 9", "A 2"],
            "TKZST": ["16310516", "1", "2"],
            "Land": [1, 9, 5],
            "X_Koordinate": [626677.117, 690000.0, None],   # letzte ohne Koordinate -> raus
            "Y_Koordinate": [6023913.142, 5400000.0, None],
            "DTV": [18316.0, 90000.0, 44000.0],
            "DTVSV": [1775.0, 12000.0, 8000.0],
        }
    )


def test_bast_builds_points_from_xy(monkeypatch) -> None:
    monkeypatch.setattr(base, "read_excel_zip", _fake_excel)
    gdf = bast.normalize()

    schema.validate(gdf, where="bast")
    assert gdf.crs.to_epsg() == schema.EPSG               # 25832 -> 4326
    assert set(gdf.geom_type) == {"Point"}
    assert len(gdf) == 2                                   # die Zeile ohne X/Y fällt weg
    assert set(gdf["state"]) == {"DE"} and set(gdf["source"]) == {"bast"}
    assert set(gdf["road_class"]) == {"A"}
    assert sorted(gdf["dtv_kfz"]) == [18316, 90000]
    # grobe Lageprüfung: UTM32N-Punkt (626677,6023913) -> ~10.5E/54.3N (A1 bei Lübeck)
    p = gdf.iloc[0].geometry
    assert 9 < p.x < 12 and 53 < p.y < 55