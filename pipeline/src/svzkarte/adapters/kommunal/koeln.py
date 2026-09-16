"""Köln (NW): „KFZ Zaehlstellen und Werte Koeln" — Knotenpunktzählungen auf Netzkanten (LINIEN).

Offene Daten Köln (Amt für Verkehrsmanagement), dl-de/zero-2.0. Das Shapefile-ZIP
`Zaehldaten_2016_2019_link` ist ein VISUM-Netzexport (22.988 Kanten, DHDN/GK Zone 2
mit TOWGS84 im .prj): je Kante die Werte pro RICHTUNG und Jahr — `K_<Jahr>_24H`
(Hinrichtung) und `R_K_<Jahr>…` (Gegenrichtung; DBF-gekürzte Namen wie `R_K_2016~2`).
Werte sind DTVw (werktags, Kfz/24h), hochgerechnet aus Video-Knotenzählungen
(6–10 / 11–14 / 15–19 Uhr). Nur ~1.500 Kanten tragen überhaupt Werte; der Rest ist
reines Netz und entfällt. (Das ältere ZIP 2010–2016 ist nicht integriert.)

Regel je Kante: jüngstes Jahr, in dem BEIDE Richtungen gezählt sind (Summe = Querschnitt);
sonst jüngstes Jahr mit einer gezählten Richtung (Einbahn). year = gewähltes Jahr je
Feature (`year_from`). Quelle ohne Straßenklasse -> G (städtisches Netz); `name` = STR_NAME.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "NW"
_CODE = "koeln"
_LAYER = "Zaehldaten_2016_2019_link"     # das ZIP enthält auch …_node (Knoten, Punkte)
_FWD_RE = re.compile(r"^K_(\d{4})_24H$")  # Hinrichtung, z.B. K_2019_24H
_REV_RE = re.compile(r"^R_K_(\d{4})")     # Gegenrichtung, z.B. R_K_2019~5 (DBF-gekürzt)

FIELD_MAP = {            # (abgeleitete) Spalte -> kanonische Spalte
    "dtv_kfz": "dtv_kfz",
    "NO": "station_id",
    "STR_NAME": "name",
}


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def _pick_year(g: GeoDataFrame) -> GeoDataFrame:
    """Je Kante DTVw + Jahr wählen: jüngstes Jahr mit beiden Richtungen, sonst mit einer."""
    import numpy as np
    import pandas as pd

    fwd = {int(m.group(1)): c for c in g.columns if (m := _FWD_RE.match(str(c)))}
    rev = {int(m.group(1)): c for c in g.columns if (m := _REV_RE.match(str(c)))}
    years = sorted(set(fwd) & set(rev), reverse=True)
    if not years:
        raise ValueError(f"{_CODE}: keine K_<Jahr>_24H/R_K_<Jahr>-Spalten in {list(g.columns)}")

    dtv = pd.Series(np.nan, index=g.index, dtype="float64")
    year = pd.Series(np.nan, index=g.index, dtype="float64")
    for require_both in (True, False):          # 1. beide Richtungen, 2. eine Richtung
        for y in years:                          # jüngstes Jahr zuerst
            k = pd.to_numeric(g[fwd[y]], errors="coerce")
            r = pd.to_numeric(g[rev[y]], errors="coerce")
            ok = (k.notna() & r.notna()) if require_both else (k.notna() | r.notna())
            sel = ok & dtv.isna()
            dtv[sel] = (k.fillna(0) + r.fillna(0))[sel]
            year[sel] = y
    out = g.assign(dtv_kfz=dtv, year=year)
    return out[out["dtv_kfz"].notna()]


def normalize() -> GeoDataFrame:
    """Kanten-Shapefile (GK2) -> Kanten mit DTVw (beide Richtungen summiert), EPSG:4326."""
    cfg = _cfg()
    g = base.fetch_zip(cfg["url"], layer=_LAYER)
    g = _pick_year(g)
    g["NO"] = g["NO"].astype(str)   # station_id ist im Schema ein String
    return base.to_canonical(
        g,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTVw"),
        year_from="year",
        road_class="G",
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
