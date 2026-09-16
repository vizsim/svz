"""Golden-Test Köln (Kommune, Linien): VISUM-Kanten mit Richtungswerten je Jahr.

Fixiert: Jahreswahl je Kante (jüngstes Jahr mit beiden Richtungen vor jüngerem Jahr mit
nur einer), Summe beider Richtungen, Kanten ohne Werte entfallen, GK2 -> 4326,
level=kommune / DTVw / road_class G / name aus STR_NAME.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base
from svzkarte.adapters.kommunal import koeln


def _fake_zip(*_a, **_k) -> gpd.GeoDataFrame:
    nan = float("nan")
    return gpd.GeoDataFrame(
        {
            "NO": [2070, 2030, 2010, 1010],
            "STR_NAME": ["Aachener Str.", "Aachener Str.", "Aachener Str.", "Aachener Glacis"],
            # 2070: 2016 beide Richtungen, 2019 nur Hinrichtung -> 2016 (Querschnitt) gewinnt
            "K_2016_24H": [21051, nan, nan, nan],
            "K_2019_24H": [30000, 13015, nan, nan],
            "R_K_2016~2": [15595, nan, nan, nan],
            "R_K_2019~5": [nan, 14000, 14650, nan],   # 2030: 2019 beide; 2010: nur Gegenrichtung
            "geometry": [
                LineString([(2568104, 5636313), (2568204, 5636313)]),
                LineString([(2568104, 5636413), (2568204, 5636413)]),
                LineString([(2568104, 5636513), (2568204, 5636513)]),
                LineString([(2568104, 5636613), (2568204, 5636613)]),  # 1010: keine Werte
            ],
        },
        crs="EPSG:31466",   # DHDN / Gauß-Krüger Zone 2 (wie das Shapefile)
    )


def test_koeln_year_pick_and_direction_sum(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_zip", _fake_zip)
    gdf = koeln.normalize().sort_values("station_id").reset_index(drop=True)

    schema.validate(gdf, where="koeln")
    assert gdf.crs.to_epsg() == schema.EPSG
    assert set(gdf.geom_type) == {"LineString"}
    assert len(gdf) == 3                                       # 1010 ohne Werte fällt weg
    assert set(gdf["level"]) == {"kommune"} and set(gdf["state"]) == {"NW"}
    assert set(gdf["metric"]) == {"DTVw"} and set(gdf["road_class"]) == {"G"}
    by_id = {r.station_id: (r.dtv_kfz, r.year) for r in gdf.itertuples()}
    assert by_id["2070"] == (21051 + 15595, 2016)   # beide Richtungen schlagen 2019-einseitig
    assert by_id["2030"] == (13015 + 14000, 2019)
    assert by_id["2010"] == (14650, 2019)           # nur eine Richtung -> so übernehmen
    assert set(gdf["name"]) == {"Aachener Str."}
    # Köln liegt bei ~6.9° O / 50.9° N -> GK2-Reprojektion stimmt.
    x, y = gdf.geometry.iloc[0].coords[0]
    assert 6.7 < x < 7.2 and 50.8 < y < 51.1
