"""Brandenburg: Landesbetrieb Straßenwesen, SVZ 2021 (Geoportal/INSPIRE-WFS).

Live verifiziert (Juni 2026): nativer deegree-WFS `zaehlstellen_wfs`, FeatureType
`app:verkehrsstaerke_2021` — trägt Geometrie UND Werte in einer Schicht (2315
MultiLineStrings, EPSG:25833, nur GML). Felder: KFZ (DTV Kfz), DTV_SV, klasse
(A/B/L/K), strasse ("L711"), zaehlstellennummer. DTV = alle Tage (Mo–So).

NICHT der `su-vector_zaehlstellen_wfs` (INSPIRE-harmonisiert, ohne DTV-Werte) und
nicht `strassennetz_wfs` (nur Netzgeometrie).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "BB"
_CODE = "bb"

TYPENAME = "app:verkehrsstaerke_2021"
_SRC_CRS = 25833         # ETRS89/UTM33N; GML nur -> output_format=None, src_crs setzen

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "KFZ": "dtv_kfz",
    "DTV_SV": "dtv_sv",
    "SV_KFZ": "sv_anteil",    # Schwerverkehrsanteil (%)
    "strasse": "road_no",     # z.B. "L711", "B 1"
    "zaehlstellennummer": "station_id",
}
_CLASS = {"A": "A", "B": "B", "L": "L", "K": "K"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "L")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """Verkehrsstärke-WFS (GML, EPSG:25833) -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    src = base.fetch_wfs(cfg["url"], TYPENAME, output_format=None, src_crs=_SRC_CRS)
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
