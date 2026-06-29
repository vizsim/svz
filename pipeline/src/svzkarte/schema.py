"""Kanonisches Zielschema für Verkehrsmengen/SVZ.

Jeder Adapter mappt seine Quelle auf *genau* diese Spalten (alles andere wird
verworfen). `validate(gdf)` ist der Vertrag zwischen Adaptern und merge/tiles:
Pflichtfelder vorhanden, Enums eingehalten, CRS == 4326. Wird im Build vor dem
Merge und nach dem Merge gefahren — eine kaputte Quelle fällt früh auf.
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
    "metric",      # "DTV" | "DTVw" — alle Tage vs. nur Werktage (NIE zusammen einfärben)
    "year",        # int — Bezugsjahr
    "road_class",  # "A" | "B" | "L" | "K" | "G"
    "road_no",     # str | None — z.B. "B10", "L1187"
    "station_id",  # str | None — Zählstellennummer der Quelle
    "state",       # str — "BW", "BY", …
    "source",      # str — Schlüssel in sources.yaml
    "license",     # str — "dl-de/by-2.0", "dl-de/zero-2.0", "CC-BY-4.0", …
]

# Felder, die immer gesetzt sein müssen (keine reine None-Spalte erlaubt).
REQUIRED: list[str] = ["metric", "year", "road_class", "state", "source", "license"]

METRICS: frozenset[str] = frozenset({"DTV", "DTVw"})
ROAD_CLASSES: frozenset[str] = frozenset({"A", "B", "L", "K", "G"})

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

    bad_metric = set(gdf["metric"].unique()) - METRICS
    if bad_metric:
        raise SchemaError(f"{where}: ungültige metric {bad_metric}, erlaubt {sorted(METRICS)}")

    bad_class = set(gdf["road_class"].unique()) - ROAD_CLASSES
    if bad_class:
        raise SchemaError(
            f"{where}: ungültige road_class {bad_class}, erlaubt {sorted(ROAD_CLASSES)}"
        )

    if gdf.geometry.isna().any() or gdf.geometry.is_empty.any():
        raise SchemaError(f"{where}: Null-/leere Geometrien (vor write_fgb filtern)")

    return gdf
