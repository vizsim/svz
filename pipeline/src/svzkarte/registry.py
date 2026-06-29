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
    "be": "svzkarte.adapters.be",
    "ni": "svzkarte.adapters.ni",
    "by": "svzkarte.adapters.by",
}

# Recherchiert, aber noch offen (Zugangsart aus SVZ_Quellen_Bundeslaender.md).
PLANNED: dict[str, str] = {
    "bb": "Brandenburg — gegebener WFS = nur Netzgeometrie (keine DTV); LS-Dienst noch finden",
    "hh": "Hamburg — WFS/GML, teils DTVw, dl-de/by-2.0",
    "nw": "NRW — Shape/Atom-Feed, dl-de/by-2.0",
    "sn": "Sachsen — nur WMS (ttsib, kein WFS); GDI-SBV-WFS evtl. separat",
    "st": "Sachsen-Anhalt — Netz-WFS + Excel-Werte, dl-de/by-2.0",
    "sl": "Saarland — WMS/WFS, offen (INSPIRE)",
    "sh": "Schleswig-Holstein — WFS, CC-BY 4.0",
    "th": "Thüringen — WFS (Zählstellenbereiche), dl-de/by-2.0",
    "bw": "Baden-Württemberg — Excel (CKAN) + Join Zählstellen-Geometrie, dl-de/by-2.0",
    "mv": "Mecklenburg-Vorpommern — WFS (SVZ 2015), dl-de/by-2.0 (prüfen)",
    "rp": "Rheinland-Pfalz — nur WMS (kein WFS/Vektor); Service 393 defekt → zurückgestellt",
    # Nur Viewer/PDF, vorerst zurückgestellt: HB (Bremen), HE (Hessen) -> A/B via BASt.
}

# Reihenfolge für `build all` (nur implementierte).
ORDER: list[str] = ["be", "ni", "by"]


def normalize_fn(code: str) -> Callable[[], GeoDataFrame]:
    """Lädt das Adapter-Modul und gibt dessen `normalize`-Funktion zurück."""
    if code not in REGISTRY:
        raise KeyError(code)
    mod = importlib.import_module(REGISTRY[code])
    return mod.normalize
