"""Bayern: Bayerische Straßenbauverwaltung (BAYSIS), SVZ 2021 Zählstellenbereiche.

Live verifiziert (Juni 2026): ArcGIS-Server-WFS, FeatureType
`BAYSIS_Verkehrsdaten:svz2021_zaehlstellenbereiche` (9431 MultiLineStrings,
liefert GEOJSON direkt in EPSG:4326). Felder: DTV_Kfz/DTV_SV, Straßenklasse
(A/B/St/K), Straße ("B 285"), Zählstelle. DTV = alle Tage (Mo–So).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "BY"
_CODE = "by"

TYPENAME = "BAYSIS_Verkehrsdaten:svz2021_zaehlstellenbereiche"

FIELD_MAP = {            # Quell-Spalte (mit Umlauten!) -> kanonische Spalte
    "DTV_Kfz": "dtv_kfz",
    "DTV_SV": "dtv_sv",
    "Straße": "road_no",      # z.B. "B 285", "St 2294"
    "Zählstelle": "station_id",
}
# Straßenklasse-Domäne im Dienst: K, St (Staatsstraße = Landesstraße -> L), B, A.
_CLASS = {"A": "A", "B": "B", "St": "L", "K": "K"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "L")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """BAYSIS-WFS (GEOJSON) -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    src = base.fetch_wfs(cfg["url"], TYPENAME, output_format="GEOJSON")
    return base.to_canonical(
        src,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="Straßenklasse",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
