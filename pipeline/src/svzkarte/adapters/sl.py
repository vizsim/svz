"""Saarland: LfS, SVZ-Zählstellen als PUNKTE (geoportal.saarland.de ArcGIS-WFS).

Live verifiziert (Juni 2026): FeatureType `Verkehr_WFS:SVZ_Zaehlstellen` über die
ArcGIS-Backend-URL (der Mapbender-Proxy blockt GetFeature). GEOJSON, EPSG:4326,
Punkt-Geometrie. Felder: DTV/DTVSV, Str ("L 375"), TKZST (Zählstellennummer).
road_class wird aus dem Str-Präfix abgeleitet (A/B/L/K).

Punkt-Quelle -> landet im merge in svz_points.fgb (eigener Frontend-Kreislayer).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "SL"
_CODE = "sl"

TYPENAME = "Verkehr_WFS:SVZ_Zaehlstellen"

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "DTV": "dtv_kfz",
    "DTVSV": "dtv_sv",
    "Str": "road_no",         # z.B. "L 375", "B268"
    "TKZST": "station_id",
}


def _road_class(v: object) -> str:
    s = str(v).strip().upper()
    c = s[0] if s else ""
    return c if c in ("A", "B", "L", "K") else "L"


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """SVZ-Zählstellen (Punkte, EPSG:4326) -> kanonisches Schema."""
    cfg = _cfg()
    # srs=CRS:84: dieser ArcGIS-WFS tauscht bei EPSG:4326 auf lat,lon -> lon,lat erzwingen.
    src = base.fetch_wfs(cfg["url"], TYPENAME, output_format="GEOJSON", srs="CRS:84")
    return base.to_canonical(
        src,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="Str",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
