"""Rheinland-Pfalz: LBM, SVZ-Zählstellenbereiche (DTV) über das GeoPortal RLP.

Referenz-Adapter (das Muster zum Kopieren). Quelle ist der WFS hinter
`spatial-objects/393` (die Landing-Seite exponiert WFS-GetCapabilities; der
typename trägt das `DTV_WFS:`-Präfix). Zugang/Jahr/Lizenz kommen aus
config/sources.yaml → sources.rp.

LIVE ZU BESTÄTIGEN (Stand Juni 2026 wirft Service 393 serverseitig
„Wfs object could not be created from db!" — vermutlich temporär):
  * TYPENAME: exakter FeatureType aus GetCapabilities (DTV_WFS:SVZ…_Zaehlstellenbereiche)
  * FIELDS:   Quell-Spaltennamen aus DescribeFeatureType (DTV / DTV_SV / strasse / klasse)
Beide sind unten als Konstanten zentralisiert — bei erreichbarem Dienst nur hier anpassen.
Verifikation:
  curl '…/spatial-objects/393?service=WFS&request=GetCapabilities&version=2.0.0&f=xml'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "RP"
_CODE = "rp"

# --- am Dienst zu bestätigen (siehe Modul-Docstring) ---
TYPENAME = "DTV_WFS:SVZ2021_Zaehlstellenbereiche"
FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "DTV": "dtv_kfz",
    "DTV_SV": "dtv_sv",
    "strasse": "road_no",
    "zst_nr": "station_id",
}
ROAD_CLASS_FIELD = "klasse"            # Quell-Spalte mit der Straßenklasse
ROAD_CLASS_MAP = {                     # Quellwert -> kanonisches Enum (A/B/L/K/G)
    "A": "A", "B": "B", "L": "L", "K": "K",
    "Bundesstraße": "B", "Landesstraße": "L", "Kreisstraße": "K",
}


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """WFS-Zählstellenbereiche -> kanonisches Schema (EPSG:4326)."""
    cfg = _cfg()
    src = base.fetch_wfs(cfg["url"], TYPENAME)
    return base.to_canonical(
        src,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from=ROAD_CLASS_FIELD,
        road_class_map=ROAD_CLASS_MAP,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
