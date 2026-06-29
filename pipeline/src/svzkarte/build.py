"""Build-Orchestrierung je Land: normalize() -> validate -> data/interim/<land>.fgb.

`build_all` ist fehlertolerant: ein Land, dessen Dienst down ist oder dessen Adapter
wirft, darf den Gesamt-Build nicht killen — Fehler werden gesammelt und am Ende
gemeldet (Muster wie die OBS-Portal-Skips in `unfallkarte`). `merge` baut dann aus
dem, was da ist.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from svzkarte import registry, schema
from svzkarte.adapters import base
from svzkarte.config import get_paths


@dataclass
class BuildResult:
    code: str
    fgb: Path | None
    n: int = 0
    error: str | None = None


def build_land(code: str) -> BuildResult:
    """Ein Land: Adapter normalize() -> schema.validate -> FlatGeobuf."""
    normalize = registry.normalize_fn(code)
    gdf = normalize()
    schema.validate(gdf, where=code)
    dest = get_paths().interim_fgb(code)
    fgb, n = base.write_fgb(gdf, dest)
    return BuildResult(code=code, fgb=fgb, n=n)


def build_all() -> list[BuildResult]:
    """Alle implementierten Länder (registry.ORDER); sammelt Fehler statt abzubrechen."""
    results: list[BuildResult] = []
    for code in registry.ORDER:
        try:
            res = build_land(code)
            print(f"  {code}: {res.n} Features -> {res.fgb}")
        except Exception as exc:  # noqa: BLE001 — bewusst fehlertolerant je Land
            res = BuildResult(code=code, fgb=None, error=f"{type(exc).__name__}: {exc}")
            print(f"  {code}: FEHLER {res.error}")
        results.append(res)
    return results
