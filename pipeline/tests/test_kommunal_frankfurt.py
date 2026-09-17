"""Golden-Test Frankfurt am Main (Kommune, Linien): WFS-Layer je Fahrzeugart, Join über str_nr.

Fixiert: SV = Lkw mit + Lkw ohne Anhänger über `str_nr` (Geometrie im Lkw-Layer gedreht,
Layer decken nicht alle Abschnitte ab -> dtv_sv leer), Jahr je Feature aus `zaehldatum`,
metric 24h, Straßenklasse aus dem Namen inkl. Buchstaben-Suffix ("B 40a"), 0 Kfz -> leer.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.adapters.kommunal import frankfurt

_G = {
    62: LineString([(463351.6, 5549476.5), (463197.8, 5549470.1)]),
    900: LineString([(476000.0, 5553000.0), (476100.0, 5553050.0)]),
    901: LineString([(470000.0, 5550000.0), (470080.0, 5550010.0)]),
    902: LineString([(477000.0, 5552000.0), (477050.0, 5552040.0)]),
}
_NAME = {62: "Hofheimer Straße", 900: "A 661", 901: "B 40a", 902: "Kaiserstraße"}
_DATE = {62: "2022-09-20", 900: "2022-09-20", 901: "2019-09-19", 902: "2023-04-25"}

_VALUES = {   # typename -> {str_nr: mittl_bel}
    "opendata_zaehlstellen:zs_kfz24": {62: 12239, 900: 111360, 901: 8000.5, 902: 0},
    "opendata_zaehlstellen:zs_lkw24": {900: 5020, 62: 89},               # andere Reihenfolge
    "opendata_zaehlstellen:zs_lkw_ohneanhaenger24": {62: 141, 900: 3729, 902: 14.5},
}


def _layer(typename: str) -> gpd.GeoDataFrame:
    vals = _VALUES[typename]
    flip = typename != "opendata_zaehlstellen:zs_kfz24"     # Lkw-Layer: Richtung gedreht
    return gpd.GeoDataFrame(
        {
            "str_nr": list(vals),
            "mittl_bel": list(vals.values()),
            "str_name": [_NAME[k] for k in vals],
            "zaehldatum": pd.to_datetime([_DATE[k] for k in vals]),
            "zp_nr": [None] * len(vals),
            "geometry": [_G[k].reverse() if flip else _G[k] for k in vals],
        },
        crs="EPSG:25832",
    )


def test_frankfurt_join_and_metric(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", lambda _url, tn, **_k: _layer(tn))
    gdf = schema.validate(frankfurt.normalize(), where="frankfurt").set_index("station_id")

    assert len(gdf) == 4 and set(gdf.geom_type) == {"LineString"}
    assert set(gdf["level"]) == {"kommune"} and set(gdf["metric"]) == {"24h"}
    assert set(gdf["state"]) == {"HE"} and set(gdf["license"]) == {"dl-de/by-2.0"}
    assert gdf.total_bounds[0] > 8 and gdf.total_bounds[3] < 51          # nach 4326 reprojiziert

    hof, a661, b40a, kaiser = gdf.loc["62"], gdf.loc["900"], gdf.loc["901"], gdf.loc["902"]
    assert hof["name"] == "Hofheimer Straße" and hof["road_class"] == "G"
    assert pd.isna(hof["road_no"])
    assert hof["dtv_kfz"] == 12239 and hof["dtv_sv"] == 89 + 141 and hof["year"] == 2022
    assert a661["road_class"] == "A" and a661["road_no"] == "A 661"
    assert a661["dtv_sv"] == 5020 + 3729
    assert b40a["road_class"] == "B" and b40a["road_no"] == "B 40a" and b40a["year"] == 2019
    assert b40a["dtv_kfz"] == 8000 and pd.isna(b40a["dtv_sv"])           # kein Lkw-Wert -> leer
    assert pd.isna(kaiser["dtv_kfz"]) and kaiser["dtv_sv"] == 14        # 0 Kfz = keine Angabe
    assert kaiser["year"] == 2023
