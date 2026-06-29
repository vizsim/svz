"""Nordrhein-Westfalen: Straßen.NRW, Verkehrswerte 2019 (opengeodata.nrw.de).

Live verifiziert (Juni 2026): INSPIRE-Atom-Feed verlinkt direkte Shapefile-ZIPs auf
opengeodata.nrw.de; `Verkehrswerte2019HR_EPSG25832_Shape.zip` trägt Geometrie UND
Werte (13858 LineStrings, EPSG:25832). DTV nach Tagestyp: A=alle Tage, W=Werktage,
U/S=Ferien/Sonderzähltage; wir nehmen die A-Variante (DTV, Mo–So).

Felder: DTVKFZA (DTV Kfz), DTVSVA (DTV Schwerverkehr), STRKL (B/L/K), STRBEZ
("L593"), ZSTNR (Zählstelle). Netz ohne Autobahnen (die liegen bei Autobahn GmbH/BASt).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "NW"
_CODE = "nw"

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "DTVKFZA": "dtv_kfz",     # Kfz, alle Tage
    "DTVSVA": "dtv_sv",       # Schwerverkehr, alle Tage
    "STRBEZ": "road_no",      # z.B. "L593", "B54"
    "ZSTNR": "station_id",
}
_CLASS = {"A": "A", "B": "B", "L": "L", "K": "K"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "L")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """Verkehrswerte-Shapefile (ZIP, EPSG:25832) -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    src = base.fetch_zip(cfg["url"])
    return base.to_canonical(
        src,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="STRKL",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
