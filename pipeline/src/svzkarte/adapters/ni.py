"""Niedersachsen: NLStBV, SVZ-Zählstellenbereiche 2021 (INSPIRE-Downloadservice).

Live verifiziert (Juni 2026): der Atom-/Downloadservice liefert ein ZIP mit
Shapefile `svz_zaehlst-bereiche_2021.shp` (2819 Segmente, EPSG:25832, Linien).
Felder: dtv21/dtvsv21 (DTV 2021 Kfz/SV), strkl (A/B/L), strbez ("A 1"), zstnr.
DTV = alle Tage (Mo–So) — direkt mit den anderen DTV-Ländern vergleichbar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "NI"
_CODE = "ni"

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "dtv21": "dtv_kfz",
    "dtvsv21": "dtv_sv",
    "strbez": "road_no",      # z.B. "A 1", "B 6", "L 410"
    "zstnr": "station_id",
}
_CLASS = {"A": "A", "B": "B", "L": "L", "K": "K", "G": "G"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "L")  # NI-Netz ist A/B/L; Fallback L


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """ZIP/Shapefile -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    src = base.fetch_zip(cfg["url"])
    return base.to_canonical(
        src,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="strkl",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
