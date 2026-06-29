"""Golden-Test Thüringen: ZstBer-Linien + VMenge-Werte über Composite-Key joinen.

Ohne Netz: base.fetch_wfs liefert je typename die Linien- bzw. Werte-Schicht
(EPSG:25832, dtv als String). Fixiert den Join (zst_nr,von_stat,bis_stat),
die String->Int-Coercion und die Reprojektion.
"""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base, th


def _fake_wfs(_url: str, typename: str, **_k) -> gpd.GeoDataFrame:
    if "ZstBer" in typename:  # Linien, ohne DTV
        return gpd.GeoDataFrame(
            {
                "zst_nr": ["50280102", "51374322", "99999999"],
                "von_stat": ["0", "0", "0"],
                "bis_stat": ["9665", "3492", "100"],
                "str_name": ["A 4", "A 9", "L 1044"],
                "str_klasse": ["A", "A", "L"],
                "geometry": [
                    LineString([(600000, 5600000), (600300, 5600000)]),
                    LineString([(610000, 5610000), (610300, 5610000)]),
                    LineString([(620000, 5620000), (620100, 5620000)]),
                ],
            },
            crs="EPSG:25832",
        )
    # VMenge: Werte (Polygongeometrie egal, wird verworfen); 99999999 fehlt -> dtv null
    return gpd.GeoDataFrame(
        {
            "zst_nr": ["50280102", "51374322"],
            "von_stat": ["0", "0"],
            "bis_stat": ["9665", "3492"],
            "dtv_kfz": ["48000.0", "66587.0"],   # String -> Int
            "dtv_sv": ["9000.0", "12793.0"],
            "geometry": [
                LineString([(600000, 5600000), (600300, 5600000)]),
                LineString([(610000, 5610000), (610300, 5610000)]),
            ],
        },
        crs="EPSG:25832",
    )


def test_th_join_and_normalize(monkeypatch) -> None:
    monkeypatch.setattr(base, "fetch_wfs", _fake_wfs)
    gdf = th.normalize().sort_values("station_id").reset_index(drop=True)

    schema.validate(gdf, where="th")
    assert gdf.crs.to_epsg() == schema.EPSG               # 25832 -> 4326
    assert len(gdf) == 3                                   # alle ZstBer-Linien bleiben
    assert set(gdf["state"]) == {"TH"} and set(gdf["year"]) == {2015}
    assert list(gdf["road_class"]) == ["A", "A", "L"]
    assert list(gdf["dtv_kfz"].dropna()) == [48000, 66587]   # gejoint + coerct
    assert gdf["dtv_kfz"].isna().sum() == 1                   # 99999999 ohne VMenge
