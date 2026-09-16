"""Generiert data/manifest.json: Index + Datenstand je Datensatz + Quellenliste fürs Frontend.

Gespeist aus der handgepflegten config/sources.yaml. `_sources` ist die EINZIGE
Quellenliste des Viewers: main.js baut daraus das Quellen-Panel (Name, Ebene, Land,
Jahr, Metrik, Lizenz, Zugang) und nutzt `bbox` zum Hinzoomen — main.js pflegt keine
eigene Liste mehr. `n`/`bbox` kommen aus den gebauten interim-FGB (pyogrio.read_info,
ohne Geometrien zu lesen). Für `date: auto` gilt max(year) über die gemergten FGB des
jeweiligen Datensatzes (Länder mischen 2015/2019/2021, Kommunen 2016–2026).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from svzkarte.config import get_paths, load_yaml

# Datensatz -> gemergte FGB (für den Datenstand `date: auto`); spiegelt tiles.DATASETS.
DATASET_FGBS: dict[str, list[str]] = {
    "svz_de": ["svz_lines.fgb", "svz_points.fgb"],
    "svz_bast": ["svz_bast.fgb"],
    "svz_kommunal": ["kommunal_lines.fgb", "kommunal_points.fgb"],
}

# Felder aus sources.yaml, die 1:1 ins Manifest (und damit ins Panel) gehen.
_SOURCE_KEYS = (
    "name", "level", "state", "status", "kind", "year", "metric", "license", "portal", "access",
)


def _max_year(fgb_names: list[str]) -> str | None:
    """Max. Bezugsjahr über die genannten svz-FGB (None, wenn keine gebaut)."""
    import geopandas as gpd

    years: list[int] = []
    for name in fgb_names:
        fgb = get_paths().svz / name
        if fgb.exists():
            gdf = gpd.read_file(fgb, columns=["year"])
            if len(gdf):
                years.append(int(gdf["year"].max()))
    return str(max(years)) if years else None


def _resolve_date(ds_id: str, date_spec: Any) -> str | None:
    if isinstance(date_spec, dict) and "fixed" in date_spec:
        return str(date_spec["fixed"])
    if date_spec == "auto":
        return _max_year(DATASET_FGBS.get(ds_id, []))
    return None


def _source_entry(code: str, src: dict[str, Any]) -> dict[str, Any]:
    """Panel-Metadaten einer Quelle + Featurezahl/BBox aus dem interim-FGB (falls gebaut)."""
    entry: dict[str, Any] = {k: src[k] for k in _SOURCE_KEYS if k in src}
    fgb = get_paths().interim_fgb(code)
    if fgb.exists():
        import pyogrio

        info = pyogrio.read_info(fgb)
        entry["n"] = int(info["features"])
        entry["bbox"] = [round(float(v), 4) for v in info["total_bounds"]]  # W,S,E,N (4326)
        # Jüngstes Bezugsjahr aus den Daten (Quellen mit Jahr je Feature: das YAML-Jahr ist
        # nur der Fallback, im Panel steht, was wirklich drin ist).
        years = pyogrio.read_dataframe(fgb, columns=["year"], read_geometry=False)["year"]
        if len(years):
            entry["year"] = int(years.max())
    return entry


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
        entry["vintage"] = _resolve_date(ds_id, meta.get("date"))
        entry["built"] = today
        manifest[ds_id] = entry

    # Quellenliste (alle Einträge inkl. research/blocked; der Viewer filtert status=live).
    manifest["_sources"] = {code: _source_entry(code, src) for code, src in sources.items()}

    out = paths.data / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
