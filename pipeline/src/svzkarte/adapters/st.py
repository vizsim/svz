"""Sachsen-Anhalt: LSBB, SVZ 2021 — Netzgeometrie (WFS) + DTV-Werte (Excel) gejoint.

Der GDI-LSA-Netz-WFS liefert nur Geometrie (BAB/B/L/K, Schlüssel vnk/nnk =
Netzknoten), KEINE DTV. Die DTV-Werte stehen im LSBB-Ergebnis-Excel
(`Ergebnisse_SVZ_2021.xlsx`, Blatt „Zeilenformat") mit VonNK/NachNK. Join über
(vnk,nnk) ↔ (VonNK,NachNK): von 1426 Zählabschnitten matchen ~1184 ein Netzsegment
exakt (die übrigen überspannen mehrere Netzknoten und entfallen).

EPSG:25832 (nativ angefordert). DTV = alle Tage. Lizenz dl-de/by-2.0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "ST"
_CODE = "st"

_CLASSES = ("bab", "b", "l", "k")
_SRC_CRS = 25832

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte (DTV/DTVSV aus dem Excel)
    "DTV": "dtv_kfz",
    "DTVSV": "dtv_sv",
    "Str": "road_no",         # z.B. "A 2", "B 246", "L 50"
    "TKZST": "station_id",
}
_CLASS = {"A": "A", "B": "B", "L": "L", "K": "K"}


def _road_class(v: object) -> str:
    s = str(v).strip().upper()
    return _CLASS.get(s[0], "L") if s else "L"


def _nk(v: object) -> str:
    """Netzknotennummer robust zu '4639027' normalisieren (str/float/NaN)."""
    try:
        return str(int(float(v)))
    except (ValueError, TypeError):
        return ""


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """Netz-WFS (4 Klassen) + DTV-Excel über Netzknoten -> kanonisches Schema."""
    import geopandas as gpd
    import pandas as pd

    cfg = _cfg()

    # 1) Netzgeometrie (alle Klassen) holen + (vnk,nnk)-Schlüssel.
    nets = [
        base.fetch_wfs(
            cfg["url"], f"lyr:lsa_lbbau_{c}_feature", output_format=None, src_crs=_SRC_CRS
        )
        for c in _CLASSES
    ]
    net = gpd.GeoDataFrame(pd.concat(nets, ignore_index=True), geometry="geometry", crs=nets[0].crs)
    net["_k"] = net["vnk"].map(_nk) + "_" + net["nnk"].map(_nk)
    net = net.drop_duplicates("_k")[["_k", "geometry"]]

    # 2) DTV-Werte aus dem Excel (Blatt Zeilenformat) + (VonNK,NachNK)-Schlüssel.
    df = base.read_excel_zip(cfg["values_url"], sheet="Zeilenformat")
    df["_k"] = df["VonNK"].map(_nk) + "_" + df["NachNK"].map(_nk)
    vals = df.drop_duplicates("_k")[["_k", "Str", "TKZST", "DTV", "DTVSV"]]

    # 3) Join: Geometrie (Netz) + Werte (Excel) — nur Segmente mit DTV.
    merged = net.merge(vals, on="_k", how="inner")

    return base.to_canonical(
        merged,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="Str",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
