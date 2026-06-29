"""Sachsen: GDI-SBV (LASuV/LISt, aus TT-SIB), SVZ 2021.

Live verifiziert (Juni 2026): INSPIRE-Downloaddienst liefert ein direktes
Shapefile-ZIP `DE-SN-SBV-SVZ2021.zip` (3510 LineStrings, EPSG:25833) mit Geometrie
UND Werten — klassifiziertes Straßennetz inkl. SVZ-Daten. Felder: dtv_kfzges (DTV
Kfz), dtv_sv, sv_kfz (SV-Anteil %), strasse ("A 13"), klasse (A/B/S/K), nummer.

`klasse=S` = Staatsstraße -> kanonisch L. (Der WMS/WFS `…_list_ttsib` wäre die
Dienst-Alternative; die ZIP ist der einfachere Weg.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "SN"
_CODE = "sn"

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "dtv_kfzges": "dtv_kfz",
    "dtv_sv": "dtv_sv",
    "sv_kfz": "sv_anteil",    # Schwerverkehrsanteil (%)
    "strasse": "road_no",     # z.B. "A 13", "S 177"
    "nummer": "station_id",
}
# klasse-Domäne: S (Staatsstraße -> L), B, A, K.
_CLASS = {"A": "A", "B": "B", "S": "L", "L": "L", "K": "K"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "L")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """SVZ-Shapefile (ZIP, EPSG:25833) -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    src = base.fetch_zip(cfg["url"])
    return base.to_canonical(
        src,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="klasse",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
