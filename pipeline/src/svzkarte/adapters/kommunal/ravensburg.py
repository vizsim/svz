"""Ravensburg (BW): städtische Straßenverkehrszählungen — Knotenpunkt-Zählungen als PUNKTE.

Quelle: MobiData BW, Datensatz „Straßenverkehrszählungen Stadt Ravensburg"
(Stadtplanungsamt, Sachgebiet Verkehrsplanung; GitHub-Issue #1). Eine Übersichts-Excel
mit allen Zählstellen (ID, NAME, BREITENGRAD/LAENGENGRAD) und je Zählstelle bis zu vier
Zählungen als wiederholte Spaltenblöcke KFZ_n / RAD_n / FUSSGAENGER_n / SV_n / DATUM_n.

Live verifiziert (Sept. 2026): 96 Zählstellen, 137 Zählungen 2023–2026, alle mit
WGS84-Koordinaten. Die Zählungen sind 24h-EINZELZÄHLUNGEN an einem Werktag (Di/Do),
kein Jahresmittel -> metric "24h" (nicht mit DTV gleichsetzen). Je Zählstelle wird die
JÜNGSTE Zählung übernommen (year = Zähljahr je Feature, daher `year_from`). SV wie in
der Quelle (Anteil auffällig hoch, Median ~18 % — vermutlich inkl. Lieferverkehr).
Rad-/Fußgängerzahlen kennt das Schema (noch) nicht; sie entfallen.

Straßenklasse aus dem NAME-Token (z.B. "B32_Ulmerstraße" -> B, "…_L288" -> L), sonst G
(städtisches Netz). `name` = Knotenbezeichnung ohne PLZ/Ort, z.B.
"Eywiesenstraße / Gartenstraße".
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    import pandas as pd
    from geopandas import GeoDataFrame

_STATE = "BW"
_CODE = "ravensburg"
_BLOCKS = 4                                  # KFZ_1..KFZ_4 (+ SV_n, DATUM_n)
_ROAD_RE = re.compile(r"^([ABLK])\s?(\d+)$")   # "B32", "L 288"
_PLZ_RE = re.compile(r"^\d{5}$")

FIELD_MAP = {            # (abgeleitete) Spalte -> kanonische Spalte
    "kfz": "dtv_kfz",
    "sv": "dtv_sv",
    "ID": "station_id",
    "name": "name",
    "road_no": "road_no",
}


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def _long(df: pd.DataFrame) -> pd.DataFrame:
    """Spaltenblöcke KFZ_n/SV_n/DATUM_n -> lange Tabelle (eine Zeile je Zählung)."""
    import pandas as pd

    df = df.rename(columns=lambda c: str(c).strip().upper())   # "Datum_4" -> "DATUM_4"
    key = ["ID", "NAME", "BREITENGRAD", "LAENGENGRAD"]
    parts = []
    for i in range(1, _BLOCKS + 1):
        cols = {f"KFZ_{i}": "kfz", f"SV_{i}": "sv", f"DATUM_{i}": "datum"}
        if not set(cols) <= set(df.columns):
            continue
        parts.append(df[[*key, *cols]].rename(columns=cols))
    long = pd.concat(parts, ignore_index=True)
    for c in ("kfz", "sv"):
        long[c] = pd.to_numeric(long[c], errors="coerce")   # Leerstrings -> NaN
    long["datum"] = pd.to_datetime(long["datum"], errors="coerce")
    return long[long["kfz"].notna() & long["datum"].notna()]


def _latest(long: pd.DataFrame) -> pd.DataFrame:
    """Jüngste Zählung je Zählstelle."""
    return long.sort_values("datum").groupby("ID", as_index=False).tail(1)


def _parse_name(raw: object, city: str) -> tuple[str, str | None, str]:
    """"B32_Ulmerstraße_88212_Ravensburg" -> ("B 32 / Ulmerstraße", "B 32", "B")."""
    tokens = [t.strip() for t in str(raw).split("_") if t.strip()]
    tokens = [t for t in tokens if not _PLZ_RE.match(t) and t.lower() != city.lower()]
    road_no, klass = None, "G"
    pretty = []
    for t in tokens:
        m = _ROAD_RE.match(t.replace(" ", ""))
        if m and road_no is None:
            road_no, klass = f"{m.group(1)} {m.group(2)}", m.group(1)
            pretty.append(road_no)
        else:
            pretty.append(t)
    return " / ".join(pretty), road_no, klass


def normalize() -> GeoDataFrame:
    """Übersichts-Excel (4 Zählblöcke) -> jüngste Zählung je Zählstelle als Punkt."""
    import geopandas as gpd

    cfg = _cfg()
    df = _latest(_long(base.read_excel_zip(cfg["url"]))).copy()

    parsed = [_parse_name(n, cfg.get("name", "Ravensburg")) for n in df["NAME"]]
    df["name"] = [p[0] for p in parsed]
    df["road_no"] = [p[1] for p in parsed]
    df["klasse"] = [p[2] for p in parsed]
    df["year"] = df["datum"].dt.year
    df["ID"] = df["ID"].astype(str)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["LAENGENGRAD"], df["BREITENGRAD"]),
        crs="EPSG:4326",
    )
    return base.to_canonical(
        gdf,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "24h"),
        year_from="year",
        road_class_from="klasse",
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
