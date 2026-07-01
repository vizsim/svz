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


def build_svz(*, dry_run: bool = False) -> dict[str, Path]:
    """Zwei PMTiles:
      - svz_de.pmtiles  = svz_lines.fgb (Layer `svz`) + svz_points.fgb (`svz_points`),
        per tile-join vereint (Länder).
      - svz_bast.pmtiles = svz_bast.fgb (Layer `bast`), der bundesweite BASt-Backbone,
        im Frontend separat schaltbar.
    Baut nur, was als FGB existiert.
    """
    from svzkarte.config import get_paths

    paths = get_paths()
    results: dict[str, Path] = {}

    # 1) Länder -> svz_de.pmtiles (Linien + Punkte via tile-join).
    out_de = paths.svz / "svz_de.pmtiles"
    parts: list[Path] = []
    for profile, fgb in (
        ("svz_lines", paths.svz / "svz_lines.fgb"),
        ("svz_points", paths.svz / "svz_points.fgb"),
    ):
        if not fgb.exists() and not dry_run:
            continue
        part = out_de.with_name(f"_{profile}_tmp.pmtiles")
        tippecanoe(profile, fgb, part, dry_run=dry_run)
        parts.append(part)
    if parts:
        results["svz_de"] = tile_join(out_de, parts, dry_run=dry_run)
        if not dry_run:
            for part in parts:
                part.unlink(missing_ok=True)

    # 2) BASt-Backbone -> eigenes svz_bast.pmtiles.
    bast_fgb = paths.svz / "svz_bast.fgb"
    if bast_fgb.exists() or dry_run:
        results["svz_bast"] = tippecanoe(
            "bast_points", bast_fgb, paths.svz / "svz_bast.pmtiles", dry_run=dry_run
        )

    if not results:
        raise FileNotFoundError(f"Keine svz_*.fgb in {paths.svz} — erst `svz merge`.")
    return results
