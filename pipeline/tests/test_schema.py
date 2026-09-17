"""Tests für schema.validate + base.to_canonical/write_fgb (kanonischer Vertrag)."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import LineString

from svzkarte import schema
from svzkarte.adapters import base


def _raw_utm() -> gpd.GeoDataFrame:
    # 2 Linien in UTM32N (EPSG:25832) mit Quell-Spaltennamen + Fremdspalte.
    return gpd.GeoDataFrame(
        {
            "DTV": [12000, 5000],
            "DTV_SV": [800, 300],
            "strasse": ["B10", "L1187"],
            "junk": ["x", "y"],
            "geometry": [
                LineString([(500000, 5400000), (500100, 5400000)]),
                LineString([(500000, 5400100), (500200, 5400100)]),
            ],
        },
        crs="EPSG:25832",
    )


def test_to_canonical_maps_reprojects_and_drops_foreign() -> None:
    out = base.to_canonical(
        _raw_utm(),
        mapping={"DTV": "dtv_kfz", "DTV_SV": "dtv_sv", "strasse": "road_no"},
        metric="DTV", year=2021, road_class="B",
        state="RP", source="rp", license="dl-de/by-2.0",
    )
    schema.validate(out, where="rp")          # erfüllt den Vertrag
    assert out.crs.to_epsg() == schema.EPSG    # nach 4326 reprojiziert
    assert "junk" not in out.columns           # Fremdspalte verworfen
    assert list(out["road_no"]) == ["B10", "L1187"]
    assert out["dtv_kfz"].dtype == "Int64"


def test_to_canonical_level_from_sources_and_year_from_column() -> None:
    raw = _raw_utm()
    raw["jahr"] = ["2019", 2021]                    # gemischte Typen -> Int64 je Zeile
    out = base.to_canonical(
        raw, mapping={"DTV": "dtv_kfz"},
        metric="24h", year_from="jahr", road_class="G",
        state="BW", source="ravensburg", license="dl-de/by-2.0",
    )
    schema.validate(out, where="ravensburg")
    assert list(out["year"]) == [2019, 2021]
    assert set(out["level"]) == {"kommune"}         # aus sources.yaml über `source`
    assert out["name"].isna().all()                 # optionale Spalte wird aufgefüllt


def test_to_canonical_zero_kfz_means_no_data() -> None:
    # Issue #2: Quellen kodieren „nicht gezählt" als 0 -> leer (Karte: grau „keine Angabe").
    raw = gpd.GeoDataFrame(
        {
            "DTV": [0, 0, 4200, None],
            "DTV_SV": [0, 194, 0, 0],
            "geometry": [
                LineString([(500000, 5400000 + i), (500100, 5400000 + i)]) for i in range(4)
            ],
        },
        crs="EPSG:25832",
    )
    out = base.to_canonical(
        raw, mapping={"DTV": "dtv_kfz", "DTV_SV": "dtv_sv"},
        metric="DTV", year=2019, road_class="K",
        state="NW", source="nw", license="dl-de/by-2.0",
    )
    schema.validate(out, where="nw")
    assert out["dtv_kfz"].isna().tolist() == [True, True, False, True]
    assert out["dtv_sv"].isna().tolist() == [True, False, False, True]   # Platzhalter-0 weg
    assert out["dtv_sv"].iloc[1] == 194                                  # echter SV-Wert bleibt
    assert out["dtv_kfz"].iloc[2] == 4200 and out["dtv_sv"].iloc[2] == 0  # SV 0 neben Kfz bleibt


def test_validate_rejects_bad_level() -> None:
    out = base.to_canonical(
        _raw_utm(), mapping={"DTV": "dtv_kfz"},
        metric="DTV", year=2021, road_class="B", level="stadt",
        state="RP", source="rp", license="dl-de/by-2.0",
    )
    with pytest.raises(schema.SchemaError):
        schema.validate(out)


def test_validate_rejects_bad_metric() -> None:
    out = base.to_canonical(
        _raw_utm(), mapping={"DTV": "dtv_kfz"},
        metric="DTVx", year=2021, road_class="B",
        state="RP", source="rp", license="dl-de/by-2.0",
    )
    with pytest.raises(schema.SchemaError):
        schema.validate(out)


def test_write_fgb_filters_null_geometry(tmp_path: Path) -> None:
    gdf = base.to_canonical(
        _raw_utm(), mapping={"DTV": "dtv_kfz"},
        metric="DTV", year=2021, road_class="B",
        state="RP", source="rp", license="dl-de/by-2.0",
    )
    gdf.loc[0, "geometry"] = None  # eine Null-Geometrie -> muss rausfallen
    out, n = base.write_fgb(gdf, tmp_path / "rp.fgb")
    assert out.exists() and n == 1
