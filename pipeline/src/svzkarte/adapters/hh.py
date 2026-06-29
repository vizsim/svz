"""Hamburg: BVM, Verkehrsmengen 2019 (geodienste.hamburg.de WFS).

Live verifiziert (Juni 2026): WFS `HH_WFS_Verkehrsmengen`, zwei DTV-2019-Layer, die
zusammen das Hauptnetz ergeben — `de.hh.up:verkehrsmengen_dtv_hvs_2019`
(Hauptverkehrsstraßen, 3728) + `..._dtv_bab_2019` (Autobahnen, 575). GeoJSON
(`application/geo+json`), EPSG:25832 (auf srsName=4326 sauber lon,lat).

Felder: dtv (DTV Kfz), sv (Schwerverkehrs-ANTEIL in %, nicht absolut -> sv_anteil),
strassenklasse (funktional: HVS/BAB). Es gibt keine Admin-Klasse/Straßennummer im
Datensatz; daher BAB -> A, HVS -> B (funktionale Näherung, nur Hauptnetz enthalten).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "HH"
_CODE = "hh"

TYPENAMES = (
    "de.hh.up:verkehrsmengen_dtv_hvs_2019",
    "de.hh.up:verkehrsmengen_dtv_bab_2019",
)
_FORMAT = "application/geo+json"

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "dtv": "dtv_kfz",
    "sv": "sv_anteil",       # Schwerverkehrsanteil in %
    "id": "station_id",
}
_CLASS = {"BAB": "A", "HVS": "B"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "B")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """Beide 2019-Layer (HVS + BAB) -> kanonisches Schema (EPSG:4326)."""
    import geopandas as gpd
    import pandas as pd

    cfg = _cfg()
    parts = [base.fetch_wfs(cfg["url"], tn, output_format=_FORMAT) for tn in TYPENAMES]
    src = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True), geometry="geometry", crs=parts[0].crs
    )
    return base.to_canonical(
        src,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="strassenklasse",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
