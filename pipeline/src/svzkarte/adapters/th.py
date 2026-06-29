"""Thüringen: TLBV über den Geoproxy (STRNETZ_SVZ_wfs).

Live verifiziert (Juni 2026): Dienst spricht nur **WFS 1.1.0** (nicht 2.0.0!).
Zwei Layer werden über den Schlüssel (zst_nr, von_stat, bis_stat) gejoint:
  - `tlbv:SVZ2015_ZstBer`  -> Liniengeometrie (Zählstellenbereiche), ohne DTV.
  - `tlbv:SVZ2015_VMenge`  -> dtv_kfz/dtv_sv (Geometrie dort nur Polygon-Band).
EPSG:25832 (nativ angefordert -> kein 1.1.0-Achsenproblem). Klassen A/B/L/K.

Dienstname trägt „SVZ2015", DTV-jahr-Feld = 2015. Lizenz dl-de/by-2.0 (© GDI-Th).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "TH"
_CODE = "th"

LINES = "tlbv:SVZ2015_ZstBer"
VALUES = "tlbv:SVZ2015_VMenge"
_SRC_CRS = 25832
_KEY = ["zst_nr", "von_stat", "bis_stat"]

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte (dtv_* sind schon kanonisch benannt)
    "str_name": "road_no",    # z.B. "A 4", "B 7", "L 1044"
    "zst_nr": "station_id",
}
_CLASS = {"A": "A", "B": "B", "L": "L", "K": "K"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "L")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """ZstBer-Linien + VMenge-Werte (Join) -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    zb = base.fetch_wfs(cfg["url"], LINES, version="1.1.0", output_format=None, src_crs=_SRC_CRS)
    vm = base.fetch_wfs(cfg["url"], VALUES, version="1.1.0", output_format=None, src_crs=_SRC_CRS)

    vals = vm[[*_KEY, "dtv_kfz", "dtv_sv"]].drop_duplicates(_KEY)
    merged = zb.merge(vals, on=_KEY, how="left")

    return base.to_canonical(
        merged,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="str_klasse",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
