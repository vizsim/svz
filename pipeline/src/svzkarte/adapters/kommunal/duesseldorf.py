"""Düsseldorf (NW): „Verkehrszähldaten Düsseldorf 2024" — DTVa je Straßenabschnitt (LINIEN).

Open Data Düsseldorf (Amt für Verkehrsmanagement), dl-de/zero-2.0. Hinter den DKAN-
Ressourcen steckt ein GeoServer-WFS 2.0.0 (`maps.duesseldorf.de/services/verkehrszaehlung`)
mit einem Layer je Fahrzeugart: `dtva_kfz_alle_tage` (Kfz), `dtva_lkw_oa`, `dtva_lkw_ma`,
`dtva_bus`, … (dazu `dtvw_kfz_werktag`). Jeder Layer hat dieselben 2.089 Abschnitte mit
identischer Geometrie, aber eigenen UUIDs -> Join über die Geometrie (WKB).

Werte: `belastung_gesamt_5j` (Mittel der Zählungen 2020–2024) bzw., wo nicht vorhanden,
`belastung_gesamt_10j` (2015–2024); Zeitraum steht in `zeitraum_5j`/`zeitraum_10j`
("2020 - 2024") -> year = Endjahr je Feature. DTVa = Kfz/24h Mo–So inkl. Feier-/
Ferientage, hochgerechnet aus 16h-Werktagszählungen (6–22 Uhr) -> metric DTV.
SV = Lkw ohne Anhänger + Lkw mit Anhänger + Bus (gleiche 5j/10j-Logik je Layer).
Straßenklasse aus dem Namen ("Autobahn A46", "A52 Ost", "B 8" …), sonst G; name = strasse.
Live verifiziert (Sept. 2026).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    import pandas as pd
    from geopandas import GeoDataFrame

_STATE = "NW"
_CODE = "duesseldorf"
_KFZ = "verkehrszaehlung:dtva_kfz_alle_tage"
_SV_LAYERS = (
    "verkehrszaehlung:dtva_lkw_oa",
    "verkehrszaehlung:dtva_lkw_ma",
    "verkehrszaehlung:dtva_bus",
)
_ROAD_RE = re.compile(r"\b([ABLK])\s?(\d{1,4})\b")
_YEAR_RE = re.compile(r"(\d{4})\s*$")

FIELD_MAP = {            # (abgeleitete) Spalte -> kanonische Spalte
    "dtv_kfz": "dtv_kfz",
    "dtv_sv": "dtv_sv",
    "strasse": "name",
    "road_no": "road_no",
    "_uuid": "station_id",
}


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def _pick(g: GeoDataFrame) -> tuple[pd.Series, pd.Series]:
    """Wert + Endjahr je Abschnitt: 5-Jahres-Mittel, sonst 10-Jahres-Mittel."""
    import pandas as pd

    v5 = pd.to_numeric(g["belastung_gesamt_5j"], errors="coerce")
    v10 = pd.to_numeric(g["belastung_gesamt_10j"], errors="coerce")
    y5 = g["zeitraum_5j"].astype("string").str.extract(_YEAR_RE)[0]
    y10 = g["zeitraum_10j"].astype("string").str.extract(_YEAR_RE)[0]
    use5 = v5.notna()
    return v5.where(use5, v10), pd.to_numeric(y5.where(use5, y10), errors="coerce")


def _road(name: object) -> tuple[str | None, str]:
    m = _ROAD_RE.search(str(name or ""))
    return (f"{m.group(1)} {m.group(2)}", m.group(1)) if m else (None, "G")


def _fetch(cfg: dict, typename: str) -> GeoDataFrame:
    return base.fetch_wfs(cfg["url"], typename, version="2.0.0", output_format="application/json")


def normalize() -> GeoDataFrame:
    """Kfz-Layer + SV-Layer (Lkw oA/mA, Bus) über die Geometrie gejoint -> kanonische Linien."""
    import pandas as pd

    cfg = _cfg()
    g = _fetch(cfg, _KFZ).copy()
    g["dtv_kfz"], g["year"] = _pick(g)
    g["_wkb"] = g.geometry.apply(lambda geom: geom.wkb)

    # Schwerverkehr: je Layer derselbe 5j/10j-Griff, Summe über Lkw oA + Lkw mA + Bus.
    sv = pd.Series(0.0, index=g["_wkb"].to_numpy(), dtype="float64")
    any_sv = pd.Series(False, index=sv.index)
    for tn in _SV_LAYERS:
        s = _fetch(cfg, tn)
        val, _ = _pick(s)
        part = pd.Series(val.to_numpy(), index=s.geometry.apply(lambda geom: geom.wkb).to_numpy())
        part = part[~part.index.duplicated()].reindex(sv.index)
        any_sv |= part.notna()
        sv = sv + part.fillna(0)
    g["dtv_sv"] = sv.where(any_sv).to_numpy()

    roads = [_road(n) for n in g["strasse"]]
    g["road_no"] = [r[0] for r in roads]
    g["klasse"] = [r[1] for r in roads]
    g = g[g["dtv_kfz"].notna()].drop(columns="_wkb")

    return base.to_canonical(
        g,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year_from="year",
        road_class_from="klasse",
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
