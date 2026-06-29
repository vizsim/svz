"""Generiert data/manifest.json: Index + Datenstand je Datensatz.

Gespeist aus der handgepflegten config/sources.yaml. Für `date: auto` löst dieses
Modul den Datenstand des `svz_de`-Layers als max(year) über die gemergte FGB auf
(Länder mischen 2015/2019/2021). Attribution wird je Land aus `sources` aggregiert.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from svzkarte.config import get_paths, load_yaml


def _svz_max_year() -> str | None:
    """Max. Bezugsjahr aus der gebauten svz_de.fgb (None, wenn nicht vorhanden)."""
    fgb = get_paths().svz / "svz_de.fgb"
    if not fgb.exists():
        return None
    import geopandas as gpd

    gdf = gpd.read_file(fgb, columns=["year"])
    return str(int(gdf["year"].max())) if len(gdf) else None


def _resolve_date(date_spec: Any) -> str | None:
    if isinstance(date_spec, dict) and "fixed" in date_spec:
        return str(date_spec["fixed"])
    if date_spec == "auto":
        return _svz_max_year()
    return None


def generate() -> Path:
    cfg = load_yaml("sources.yaml")
    datasets = cfg["datasets"]
    sources = cfg.get("sources", {})
    paths = get_paths()
    today = date.today().isoformat()

    manifest: dict[str, dict[str, Any]] = {}
    for ds_id, meta in datasets.items():
        entry: dict[str, Any] = {"label": meta.get("label")}
        if meta.get("attribution"):
            entry["attribution"] = meta["attribution"]
        entry["file"] = meta["file"]
        entry["present"] = (paths.data / meta["file"]).exists()
        entry["vintage"] = _resolve_date(meta.get("date"))
        entry["built"] = today
        manifest[ds_id] = entry

    # Pro-Land-Herkunft (Datenstand/Lizenz je Quelle) für die Attribution-Anzeige.
    manifest["_sources"] = {
        code: {k: src.get(k) for k in ("year", "license", "metric") if k in src}
        for code, src in sources.items()
    }

    out = paths.data / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
