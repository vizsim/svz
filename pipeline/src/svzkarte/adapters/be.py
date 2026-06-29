"""Berlin: SenMVKU, Verkehrsmengen DTVw 2023 über den gdi.berlin.de-WFS.

Live verifiziert (Juni 2026): WFS `verkehrsmengen_2023`, FeatureType
`…:dtvw2023kfz` (8337 LineStrings, EPSG:25833, liefert auf srsName=4326 korrekt
lon,lat). Der Schwerverkehr steckt in einer eigenen Schicht `…:dtvw2023lkw`; wir
joinen ihn über `link_id` als `dtv_sv` an.

Berlin liefert **DTVw** (nur Werktage) — nicht mit DTV mischbar (metric-Filter).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "BE"
_CODE = "be"

KFZ_TYPE = "verkehrsmengen_2023:dtvw2023kfz"
LKW_TYPE = "verkehrsmengen_2023:dtvw2023lkw"

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "dtvw_kfz": "dtv_kfz",
    "str_bez": "road_no",     # z.B. "B1"; bei Gemeindestraßen leer -> None
    "link_id": "station_id",  # Segment-ID
}
# strklasse-Domäne im Dienst: G (Masse), B, A, L + Einzelfälle N/P/F -> Sammel-Bucket G.
_CLASS = {"A": "A", "B": "B", "L": "L", "K": "K", "G": "G"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v), "G")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """Kfz-Verkehrsmengen + Lkw-Join -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    kfz = base.fetch_wfs(cfg["url"], KFZ_TYPE)
    lkw = base.fetch_wfs(cfg["url"], LKW_TYPE)

    # Schwerverkehr (DTVw Lkw) über die Segment-ID anhängen (dedupe gegen Fan-out).
    sv = lkw[["link_id", "dtvw_lkw"]].rename(columns={"dtvw_lkw": "dtv_sv"})
    sv = sv.drop_duplicates("link_id")
    kfz = kfz.merge(sv, on="link_id", how="left")
    kfz["str_bez"] = kfz["str_bez"].replace({"": None})  # leere Bez. -> None

    return base.to_canonical(
        kfz,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTVw"),
        year=cfg["year"],
        road_class_from="strklasse",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
