"""Golden-Test Berlin: normalize() mappt Kfz-WFS + Lkw-Join aufs kanonische Schema.

Ohne Netz: base.fetch_wfs wird ersetzt und liefert je nach typename eine synthetische
Kfz- bzw. Lkw-Schicht (Felder/CRS wie der echte gdi.berlin.de-Dienst). Fixiert das
Mapping inkl. Lkw-Join (dtv_sv), strklasse-Default (N -> G) und leerer str_bez -> None.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base, be


def _fake_wfs(_url: str, typename: str, **_kw) -> gpd.GeoDataFrame:
    if typename.endswith("kfz"):
        return gpd.GeoDataFrame(
            {
                "link_id": ["a", "b", "c"],
                "strklasse": ["B", "G", "N"],          # N ist kein Enum -> Default G
                "str_bez": ["B1", "", ""],             # leer -> None
                "str_name": ["Königstr.", "Wald", "X"],  # Fremdspalte -> verworfen
                "dtvw_kfz": [10900, 4200, 1500],
                "geometry": [
                    LineString([(13.09, 52.41), (13.10, 52.41)]),
                    LineString([(13.20, 52.50), (13.21, 52.50)]),
                    LineString([(13.30, 52.55), (13.31, 52.55)]),
                ],
            },
            crs="EPSG:4326",
        )
    return gpd.GeoDataFrame(  # Lkw-Schicht (Join über link_id), 'c' ohne Lkw-Wert
        {
            "link_id": ["a", "b"],
            "dtvw_lkw": [800, 150],
            "geometry": [
                LineString([(13.09, 52.41), (13.10, 52.41)]),
                LineString([(13.20, 52.50), (13.21, 52.50)]),
            ],
        },
        crs="EPSG:4326",
    )


def test_be_normalize_maps_and_joins(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    gdf = be.normalize().sort_values("station_id").reset_index(drop=True)

    schema.validate(gdf, where="be")
    assert list(gdf["state"]) == ["BE", "BE", "BE"]
    assert set(gdf["metric"]) == {"DTVw"} and set(gdf["year"]) == {2023}
    assert list(gdf["road_class"]) == ["B", "G", "G"]   # N -> G (Default-Bucket)
    assert list(gdf["road_no"]) == ["B1", None, None]   # leere str_bez -> None
    assert list(gdf["dtv_kfz"]) == [10900, 4200, 1500]
    assert gdf.loc[2, "dtv_sv"] is None or str(gdf.loc[2, "dtv_sv"]) == "<NA>"  # 'c' ohne Lkw
    assert list(gdf["dtv_sv"][:2]) == [800, 150]
