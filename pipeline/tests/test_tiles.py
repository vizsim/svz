"""Test: svz_lines-Profil ist korrekt auf tippecanoe-Flags verdrahtet."""

from __future__ import annotations

from svzkarte import tiles


def test_svz_lines_profile_wired() -> None:
    args = tiles._profile_args(tiles._profiles()["svz_lines"])
    assert "-l" in args and "svz" in args            # interner Layer = Frontend-Vertrag
    assert "--minimum-zoom=6" in args
    assert "--maximum-zoom=14" in args
    assert "--no-tile-size-limit" in args
    assert "--drop-densest-as-needed" in args
