"""Adapter-Registry: land-code -> Adapter-Modul (mit `normalize()`).

Muster wie `unfallkarte.scenarios.registry`. Neuer Adapter = Modul unter
`adapters/<code>.py` mit `normalize() -> GeoDataFrame` + Eintrag in REGISTRY.
PLANNED = recherchierte, noch nicht implementierte Länder (aus der Quellenübersicht).
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

# Implementiert: code -> Modulpfad (lazy import, damit `svz info` leicht bleibt).
REGISTRY: dict[str, str] = {
    "rp": "svzkarte.adapters.rp",
}

# Recherchiert, aber noch offen (Zugangsart aus SVZ_Quellen_Bundeslaender.md).
PLANNED: dict[str, str] = {
    "by": "Bayern — WFS (BAYSIS), CC-BY 4.0",
    "be": "Berlin — WFS, DTVw 2019, dl-de/zero-2.0",
    "bb": "Brandenburg — WFS (Zählstellenbereiche), dl-de/by-2.0",
    "hh": "Hamburg — WFS/GML, teils DTVw, dl-de/by-2.0",
    "ni": "Niedersachsen — INSPIRE ATOM/WFS, dl-de/by-2.0",
    "nw": "NRW — Shape/Atom-Feed, dl-de/by-2.0",
    "sn": "Sachsen — WFS, dl-de/by-2.0",
    "st": "Sachsen-Anhalt — Netz-WFS + Excel-Werte, dl-de/by-2.0",
    "sl": "Saarland — WMS/WFS, offen (INSPIRE)",
    "sh": "Schleswig-Holstein — WFS, CC-BY 4.0",
    "th": "Thüringen — WFS (Zählstellenbereiche), dl-de/by-2.0",
    "bw": "Baden-Württemberg — Excel (CKAN) + Join Zählstellen-Geometrie, dl-de/by-2.0",
    "mv": "Mecklenburg-Vorpommern — WFS (SVZ 2015), dl-de/by-2.0 (prüfen)",
    # Nur Viewer/PDF, vorerst zurückgestellt: HB (Bremen), HE (Hessen) -> A/B via BASt.
}

# Reihenfolge für `build all` (nur implementierte).
ORDER: list[str] = ["rp"]


def normalize_fn(code: str) -> Callable[[], GeoDataFrame]:
    """Lädt das Adapter-Modul und gibt dessen `normalize`-Funktion zurück."""
    if code not in REGISTRY:
        raise KeyError(code)
    mod = importlib.import_module(REGISTRY[code])
    return mod.normalize
