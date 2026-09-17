"""Frankfurt am Main (HE): „WFS Verkehrsmengen" — Kfz/24h je Straßenabschnitt (LINIEN).

Straßenverkehrsamt Frankfurt, dl-de/by-2.0 (lt. GovData/Open Data Hessen). GeoServer-WFS
2.0.0 hinter `geowebdienste.frankfurt.de/Verkehrsmengen` (Workspace `opendata_zaehlstellen`)
mit einem Layer je Fahrzeugart: `zs_kfz24` (Kfz, 530 Abschnitte), `zs_lkw24` (Lkw MIT
Anhänger), `zs_lkw_ohneanhaenger24` (Lkw ohne Anhänger), `zs_rad24` (Rad, hier ungenutzt).
Alle Layer teilen die Abschnittsnummer `str_nr` (eindeutig je Layer, identische Geometrie,
Digitalisierrichtung teils gedreht) -> Join über `str_nr`, nicht über die Geometrie.

Werte: `mittl_bel` = Querschnittswert „Mittelwerte der Jahre 2019–2023" (halbe Werte =
Mittel aus zwei Zählungen); `zaehldatum` = Zähltag, ausnahmslos Di–Do -> year je Feature.
Es sind gemittelte Werktags-24h-Zählungen, keine Hochrechnung auf ein Jahresmittel ->
metric 24h (nicht DTV/DTVw). SV = Lkw mit + Lkw ohne Anhänger (kein Bus-Layer); die
Lkw-Layer decken nur ~410 der 530 Abschnitte ab -> sonst dtv_sv leer. `mittl_bel` = 0
(3 Abschnitte) wird wie überall zu „keine Angabe" (base.to_canonical). Straßenklasse aus
dem Namen ("A 661", "B 40a", "L 3003", "K 824"), sonst G; name = str_name. Live verifiziert
(Sept. 2026; bis dahin lieferte jedes GetFeature HTTP 500).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "HE"
_CODE = "frankfurt"
_KFZ = "opendata_zaehlstellen:zs_kfz24"
_SV_LAYERS = (
    "opendata_zaehlstellen:zs_lkw24",                  # Lkw mit Anhänger
    "opendata_zaehlstellen:zs_lkw_ohneanhaenger24",    # Lkw ohne Anhänger
)
_ROAD_RE = re.compile(r"\b([ABLK])\s?(\d{1,4}[a-z]?)\b")

FIELD_MAP = {            # (abgeleitete) Spalte -> kanonische Spalte
    "mittl_bel": "dtv_kfz",
    "dtv_sv": "dtv_sv",
    "str_name": "name",
    "road_no": "road_no",
    "station_id": "station_id",
}


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def _road(name: object) -> tuple[str | None, str]:
    m = _ROAD_RE.search(str(name or ""))
    return (f"{m.group(1)} {m.group(2)}", m.group(1)) if m else (None, "G")


def _fetch(cfg: dict, typename: str) -> GeoDataFrame:
    return base.fetch_wfs(cfg["url"], typename, version="2.0.0", output_format="application/json")


def normalize() -> GeoDataFrame:
    """Kfz-Layer + Lkw-Layer (mit/ohne Anhänger) über `str_nr` gejoint -> kanonische Linien."""
    import pandas as pd

    cfg = _cfg()
    g = _fetch(cfg, _KFZ).copy()
    g["mittl_bel"] = pd.to_numeric(g["mittl_bel"], errors="coerce")
    g["year"] = pd.to_datetime(g["zaehldatum"], errors="coerce").dt.year

    # Schwerverkehr: Summe der Lkw-Layer je Abschnitt; ohne jeden Lkw-Wert bleibt dtv_sv leer.
    sv = pd.Series(0.0, index=g["str_nr"].to_numpy(), dtype="float64")
    any_sv = pd.Series(False, index=sv.index)
    for tn in _SV_LAYERS:
        s = _fetch(cfg, tn)
        part = pd.Series(
            pd.to_numeric(s["mittl_bel"], errors="coerce").to_numpy(), index=s["str_nr"].to_numpy()
        )
        part = part[~part.index.duplicated()].reindex(sv.index)
        any_sv |= part.notna()
        sv = sv + part.fillna(0)
    g["dtv_sv"] = sv.where(any_sv).to_numpy()

    roads = [_road(n) for n in g["str_name"]]
    g["road_no"] = [r[0] for r in roads]
    g["klasse"] = [r[1] for r in roads]
    g["station_id"] = g["str_nr"].astype("Int64").astype("string")
    g = g[g["mittl_bel"].notna() & g["year"].notna()]

    return base.to_canonical(
        g,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "24h"),
        year_from="year",
        road_class_from="klasse",
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
