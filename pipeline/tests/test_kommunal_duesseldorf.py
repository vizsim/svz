"""Golden-Test Düsseldorf (Kommune, Linien): WFS-Layer je Fahrzeugart, Join über Geometrie.

Fixiert: 5j-Mittel vor 10j-Mittel (+ Endjahr aus `zeitraum_*`), SV = Lkw oA + Lkw mA + Bus
über identische Geometrien (UUIDs je Layer verschieden), Straßenklasse aus dem Namen.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.adapters.kommunal import duesseldorf

_G1 = LineString([(6.78, 51.22), (6.79, 51.22)])
_G2 = LineString([(6.80, 51.23), (6.81, 51.23)])


def _layer(typename: str) -> gpd.GeoDataFrame:
    nan = float("nan")
    vals = {
        "verkehrszaehlung:dtva_kfz_alle_tage": ([12000, nan], [11000, 7434]),
        "verkehrszaehlung:dtva_lkw_oa": ([300, nan], [280, 100]),
        "verkehrszaehlung:dtva_lkw_ma": ([nan, nan], [120, 50]),
        "verkehrszaehlung:dtva_bus": ([40, nan], [35, nan]),
    }[typename]
    return gpd.GeoDataFrame(
        {
            "_uuid": [f"{typename[-6:]}-1", f"{typename[-6:]}-2"],   # je Layer eigene IDs
            "strasse": ["Autobahn A46", "Conesweg"],
            "belastung_gesamt_5j": vals[0],
            "zeitraum_5j": ["2020 - 2024", None],
            "belastung_gesamt_10j": vals[1],
            "zeitraum_10j": ["2015 - 2024", "2015 - 2024"],
            "geometry": [_G1, _G2],
        },
        crs="EPSG:4326",
    )


def test_duesseldorf_join_and_periods(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", lambda _url, tn, **_k: _layer(tn))
    gdf = duesseldorf.normalize().sort_values("name").reset_index(drop=True)

    schema.validate(gdf, where="duesseldorf")
    assert set(gdf.geom_type) == {"LineString"}
    assert set(gdf["level"]) == {"kommune"} and set(gdf["metric"]) == {"DTV"}
    a46, cones = gdf.iloc[0], gdf.iloc[1]
    assert a46["name"] == "Autobahn A46" and a46["road_class"] == "A" and a46["road_no"] == "A 46"
    assert a46["dtv_kfz"] == 12000 and a46["year"] == 2024        # 5j-Mittel
    assert a46["dtv_sv"] == 300 + 120 + 40                         # oA (5j) + mA (10j) + Bus (5j)
    assert cones["dtv_kfz"] == 7434 and cones["year"] == 2024      # nur 10j vorhanden
    assert cones["road_class"] == "G" and cones["dtv_sv"] == 100 + 50
