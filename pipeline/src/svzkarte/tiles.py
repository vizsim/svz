"""Tippecanoe-Wrapper (aus `unfallkarte` übernommen).

Profile stehen in config/tiles.yaml (keine kopierten Argumentlisten). Wenn das
Binary fehlt oder dry_run=True, wird das Kommando nur ausgegeben statt ausgeführt —
so lässt sich die Pipeline auch ohne installiertes tippecanoe prüfen.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from shutil import which
from typing import Any

from svzkarte.config import load_yaml

_CFG = "tiles.yaml"


def _profiles() -> dict[str, Any]:
    return load_yaml(_CFG)["profiles"]


def _profile_args(profile: dict[str, Any], layer_override: str | None = None) -> list[str]:
    """Übersetzt ein Profil-Dict in tippecanoe-Flags (ohne -o/Input)."""
    args: list[str] = ["--force"]
    layer = layer_override or profile.get("layer")
    if layer:
        args += ["-l", layer]
    if "minzoom" in profile:
        args.append(f"--minimum-zoom={profile['minzoom']}")
    if "maxzoom" in profile:
        args.append(f"--maximum-zoom={profile['maxzoom']}")
    if "base_zoom" in profile:
        args.append(f"--base-zoom={profile['base_zoom']}")
    if "drop_rate" in profile:
        args.append(f"--drop-rate={profile['drop_rate']}")
    if profile.get("drop_densest_as_needed"):
        args.append("--drop-densest-as-needed")
    if profile.get("coalesce"):
        args.append("--coalesce")
    if profile.get("no_feature_limit"):
        args.append("--no-feature-limit")
    if profile.get("no_tile_size_limit"):
        args.append("--no-tile-size-limit")
    if profile.get("force_feature_limit"):
        args.append("--force-feature-limit")
    if "maximum_tile_bytes" in profile:
        args.append(f"--maximum-tile-bytes={profile['maximum_tile_bytes']}")
    # Per-Zoom-Feature-Filter (Mapbox-GL-Filtersyntax, $zoom verfügbar). Damit
    # blenden wir Nebennetz mit kleiner DTV erst ab höheren Zoomstufen ein, statt
    # bei Zoom <8 das ganze Straßennetz in wenige (zu große) Kacheln zu packen.
    if "feature_filter" in profile:
        args += ["-j", json.dumps(profile["feature_filter"], separators=(",", ":"))]
    # Attribut-Typen erzwingen: tippecanoe liest FlatGeobuf-Attribute sonst als
    # Strings, was data-driven styling (interpolate über dtv_kfz) bricht.
    for name, atype in profile.get("attribute_types", {}).items():
        args.append(f"--attribute-type={name}:{atype}")
    return args


def _run(cmd: list[str], *, dry_run: bool) -> None:
    printable = " ".join(cmd)
    if dry_run or which(cmd[0]) is None:
        reason = "dry-run" if dry_run else f"'{cmd[0]}' nicht installiert"
        print(f"  [{reason}] {printable}")
        return
    print(f"  $ {printable}")
    subprocess.run(cmd, check=True)


def tippecanoe(
    profile_name: str,
    input_path: Path,
    output_path: Path,
    *,
    layer_override: str | None = None,
    dry_run: bool = False,
) -> Path:
    profile = _profiles()[profile_name]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "tippecanoe", "-o", str(output_path),
        *_profile_args(profile, layer_override), str(input_path),
    ]
    _run(cmd, dry_run=dry_run)
    return output_path


def tile_join(output_path: Path, inputs: list[Path], *, dry_run: bool = False) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["tile-join", "--force", "-o", str(output_path), *[str(p) for p in inputs]]
    _run(cmd, dry_run=dry_run)
    return output_path


# Ein PMTiles je Ebene (Frontend-Vertrag: Dateiname + Layer-Namen der Profile).
# Mehrteilige Datensätze (Linien + Punkte) werden per tile-join vereint.
DATASETS: dict[str, list[tuple[str, str]]] = {
    "svz_de": [("svz_lines", "svz_lines.fgb"), ("svz_points", "svz_points.fgb")],
    "svz_bast": [("bast_points", "svz_bast.fgb")],
    "svz_kommunal": [
        ("kommunal_lines", "kommunal_lines.fgb"),
        ("kommunal_points", "kommunal_points.fgb"),
    ],
}


def build_svz(*, dry_run: bool = False, only: set[str] | None = None) -> dict[str, Path]:
    """Ein PMTiles je Ebene (im Frontend separat schaltbar):
      - svz_de.pmtiles       Länder: svz_lines.fgb (`svz`) + svz_points.fgb (`svz_points`)
      - svz_bast.pmtiles     Bund:   svz_bast.fgb (`bast`), der BASt-Backbone
      - svz_kommunal.pmtiles Kommunen: kommunal_lines.fgb (`kommunal`) + kommunal_points.fgb
    Baut nur, was als FGB existiert; `only` beschränkt auf einzelne Datensätze
    (z.B. {"svz_kommunal"}, damit nicht jedes Mal die Länder neu gekachelt werden).
    """
    from svzkarte.config import get_paths

    paths = get_paths()
    results: dict[str, Path] = {}

    for name, spec in DATASETS.items():
        if only and name not in only:
            continue
        out = paths.svz / f"{name}.pmtiles"
        present = [
            (prof, paths.svz / fgb) for prof, fgb in spec if (paths.svz / fgb).exists() or dry_run
        ]
        if not present:
            continue
        if len(present) == 1:
            prof, fgb = present[0]
            results[name] = tippecanoe(prof, fgb, out, dry_run=dry_run)
            continue
        parts = [
            tippecanoe(prof, fgb, out.with_name(f"_{prof}_tmp.pmtiles"), dry_run=dry_run)
            for prof, fgb in present
        ]
        results[name] = tile_join(out, parts, dry_run=dry_run)
        if not dry_run:
            for part in parts:
                part.unlink(missing_ok=True)

    if not results:
        raise FileNotFoundError(f"Keine *.fgb in {paths.svz} — erst `svz merge`.")
    return results
