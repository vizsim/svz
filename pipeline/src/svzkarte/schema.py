"""Kanonisches Zielschema für Verkehrsmengen/SVZ.

Jeder Adapter mappt seine Quelle auf *genau* diese Spalten (alles andere wird
verworfen). `validate(gdf)` ist der Vertrag zwischen Adaptern und merge/tiles:
Pflichtfelder vorhanden, Enums eingehalten, CRS == 4326. Wird im Build vor dem
Merge und nach dem Merge gefahren — eine kaputte Quelle fällt früh auf.

Ebenen (`level`): Daten kommen von drei Herausgeber-Ebenen — Bund (BASt) und Länder
(Straßenbauverwaltungen) liefern die amtliche SVZ; Kommunen liefern EIGENE städtische
Zählungen (keine SVZ, andere Methodik — im Wording immer abgesetzt). `level` steuert
im merge, in welches PMTiles ein Datensatz wandert; `source` (Schlüssel in sources.yaml)
ist der Filter-Schlüssel im Frontend, `state` bleibt das Bundesland (bei Kommunen:
das Land, in dem die Stadt liegt).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

# Kanonische Spalten (Reihenfolge = Ausgabereihenfolge). `geometry` ist separat.
COLUMNS: list[str] = [
    "dtv_kfz",     # int | None  — DTV Kfz gesamt (Kfz/24h)
    "dtv_sv",      # int | None  — DTV Schwerverkehr (Kfz/24h)
    "sv_anteil",   # float | None — Schwerverkehrsanteil (%), falls Quelle nur Anteil liefert
    "metric",      # "DTV" | "DTVw" | "24h" — s. METRICS (NIE zusammen einfärben)
    "year",        # int — Bezugsjahr (je Feature; kommunale Quellen mischen Jahre)
    "road_class",  # "A" | "B" | "L" | "K" | "G"  (G = Gemeinde-/Stadtstraße bzw. Klasse unbekannt)
    "road_no",     # str | None — z.B. "B10", "L1187"
    "name",        # str | None — Straßenname / Zählstellen-Bezeichnung lt. Quelle (v.a. kommunal)
    "station_id",  # str | None — Zählstellennummer der Quelle
    "state",       # str — "BW", "BY", … (Kommunen: Land, in dem die Stadt liegt; Bund: "DE")
    "source",      # str — Schlüssel in sources.yaml (= Filter-Schlüssel im Frontend)
    "level",       # "bund" | "land" | "kommune" — Herausgeber-Ebene (s. LEVELS)
    "license",     # str — "dl-de/by-2.0", "dl-de/zero-2.0", "CC-BY-4.0", …
]

# Felder, die immer gesetzt sein müssen (keine reine None-Spalte erlaubt).
REQUIRED: list[str] = ["metric", "year", "road_class", "state", "source", "level", "license"]

# DTV  = Jahresmittel aller Tage · DTVw = Jahresmittel Werktage (Mo–Fr)
# 24h  = EINZELZÄHLUNG über 24 h an einem Werktag (kommunale Knotenzählungen), kein Mittel
METRICS: frozenset[str] = frozenset({"DTV", "DTVw", "24h"})
ROAD_CLASSES: frozenset[str] = frozenset({"A", "B", "L", "K", "G"})
LEVELS: frozenset[str] = frozenset({"bund", "land", "kommune"})

EPSG: int = 4326


class SchemaError(ValueError):
    """Verletzung des kanonischen Schemas (Spalten/Enums/CRS)."""


def validate(gdf: GeoDataFrame, *, where: str = "<gdf>") -> GeoDataFrame:
    """Prüft den kanonischen Vertrag; gibt das gdf unverändert zurück (für Verkettung).

    Raises SchemaError mit Kontext `where` (z.B. Land-Code), wenn etwas nicht passt.
    """
    missing = [c for c in COLUMNS if c not in gdf.columns]
    if missing:
        raise SchemaError(f"{where}: fehlende Spalten {missing}")

    if "geometry" not in gdf.columns or gdf.geometry.name != "geometry":
        raise SchemaError(f"{where}: keine aktive 'geometry'-Spalte")

    crs = gdf.crs
    if crs is None or crs.to_epsg() != EPSG:
        raise SchemaError(f"{where}: CRS muss EPSG:{EPSG} sein, ist {crs}")

    for col in REQUIRED:
        if gdf[col].isna().any():
            raise SchemaError(f"{where}: Pflichtfeld '{col}' enthält Nulls")

    for col, allowed in (("metric", METRICS), ("road_class", ROAD_CLASSES), ("level", LEVELS)):
        bad = set(gdf[col].unique()) - allowed
        if bad:
            raise SchemaError(f"{where}: ungültige {col} {bad}, erlaubt {sorted(allowed)}")

    if gdf.geometry.isna().any() or gdf.geometry.is_empty.any():
        raise SchemaError(f"{where}: Null-/leere Geometrien (vor write_fgb filtern)")

    return gdf
