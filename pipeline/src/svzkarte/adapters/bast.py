"""BASt-Backbone: bundesweite SVZ 2021 der Bundesfernstraßen (Autobahnen).

Füllt die Autobahn-Lücke — seit der Autobahn GmbH (2021) veröffentlichen etliche
Länder keine A-Daten mehr (NW gar keine, BE nur Reste). Die BASt (Bundesanstalt für
Straßenwesen) bündelt die SVZ der Bundesfernstraßen bundesweit; das Excel
`Autobahnen-2021.xlsx` (Blatt „Zeilenformat") trägt DTV **und** X/Y-Koordinaten
(ETRS89/UTM32N) → direkt als PUNKTE baubar, ohne Netz-Join.

state = "DE" (Bund-weiter Backbone), source = "bast". Bundesstraßen (B) sind
absichtlich NICHT dabei — die decken die Länder ab (Doppelzählung vermeiden).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "DE"
_CODE = "bast"
_SRC_CRS = 25832         # ETRS89/UTM32N (bundesweit, mit erweitertem Ostwert)

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "DTV": "dtv_kfz",
    "DTVSV": "dtv_sv",
    "Str": "road_no",         # z.B. "A 1"
    "TKZST": "station_id",
}
_CLASS = {"A": "A", "B": "B"}


def _road_class(v: object) -> str:
    s = str(v).strip().upper()
    return _CLASS.get(s[0], "A") if s else "A"


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """BASt-Autobahn-Excel (X/Y, UTM32N) -> kanonische Punkte (EPSG:4326)."""
    import geopandas as gpd
    import pandas as pd

    cfg = _cfg()
    df = base.read_excel_zip(cfg["url"], sheet="Zeilenformat")
    # nur Zählstellen mit Koordinaten -> Punktgeometrie.
    df = df[pd.to_numeric(df["X_Koordinate"], errors="coerce").notna()].copy()
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["X_Koordinate"], df["Y_Koordinate"]),
        crs=f"EPSG:{_SRC_CRS}",
    )
    return base.to_canonical(
        gdf,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="Str",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
