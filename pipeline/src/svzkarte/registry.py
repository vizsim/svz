"""Adapter-Registry — abgeleitet aus config/sources.yaml (keine zweite Liste mehr).

Jede Quelle mit `status: live` hat einen Adapter mit `normalize() -> GeoDataFrame`.
Modulpfad per Konvention aus Code + Ebene:
  - Länder/Bund:  svzkarte.adapters.<code>            (be.py, by.py, bast.py, …)
  - Kommunen:     svzkarte.adapters.kommunal.<code>   (ravensburg.py, koeln.py, …)
`adapter:` in sources.yaml überschreibt den Pfad. Neue Quelle = YAML-Eintrag + Datei;
Build-Reihenfolge = Reihenfolge in sources.yaml. PLANNED = alle nicht-live Einträge
(research/blocked) für `svz info`.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_KOMMUNAL_PKG = "svzkarte.adapters.kommunal"
_LAND_PKG = "svzkarte.adapters"


def module_for(code: str, cfg: dict[str, Any]) -> str:
    """Adapter-Modulpfad einer Quelle (Konvention nach Ebene, `adapter:` überschreibt)."""
    if cfg.get("adapter"):
        return str(cfg["adapter"])
    pkg = _KOMMUNAL_PKG if cfg.get("level") == "kommune" else _LAND_PKG
    return f"{pkg}.{code}"


def _load() -> tuple[dict[str, str], dict[str, str]]:
    sources = load_yaml("sources.yaml")["sources"]
    live = {c: module_for(c, s) for c, s in sources.items() if s.get("status") == "live"}
    planned = {
        c: f"{s.get('name', c)} — {s.get('status')} ({s.get('kind', '?')})"
        for c, s in sources.items()
        if s.get("status") != "live"
    }
    return live, planned


# Implementiert: code -> Modulpfad (lazy import, damit `svz info` leicht bleibt).
REGISTRY: dict[str, str]
# Recherchiert, aber (noch) nicht live: code -> Kurzbeschreibung.
PLANNED: dict[str, str]
REGISTRY, PLANNED = _load()

# Reihenfolge für `build all` = Reihenfolge in sources.yaml (nur live).
ORDER: list[str] = list(REGISTRY)


def by_level(level: str) -> list[str]:
    """Live-Quellen einer Ebene (bund/land/kommune) in Build-Reihenfolge."""
    sources = load_yaml("sources.yaml")["sources"]
    return [c for c in ORDER if sources[c].get("level") == level]


def normalize_fn(code: str) -> Callable[[], GeoDataFrame]:
    """Lädt das Adapter-Modul und gibt dessen `normalize`-Funktion zurück.

    Generische Portal-Adapter (ein Modul für viele Quellen im selben Format, z.B.
    `kommunal.mobidata_bw`) deklarieren `normalize(code)`; dann wird der Quellen-Code
    gebunden. Klassische Adapter haben `normalize()` ohne Parameter.
    """
    import functools
    import inspect

    if code not in REGISTRY:
        raise KeyError(code)
    mod = importlib.import_module(REGISTRY[code])
    fn = mod.normalize
    if inspect.signature(fn).parameters:
        return functools.partial(fn, code)
    return fn
