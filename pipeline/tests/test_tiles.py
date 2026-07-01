"""Test: svz_lines-Profil ist korrekt auf tippecanoe-Flags verdrahtet."""

from __future__ import annotations

from svzkarte import tiles


def test_svz_lines_profile_wired() -> None:
    args = tiles._profile_args(tiles._profiles()["svz_lines"])
    assert "-l" in args and "svz" in args            # interner Layer = Frontend-Vertrag
    assert "--minimum-zoom=5" in args
    assert "--maximum-zoom=14" in args
    assert "--no-tile-size-limit" in args
    assert "--drop-densest-as-needed" in args
    # Zahlen müssen als int ins Tile (sonst bricht data-driven styling im Frontend).
    assert "--attribute-type=dtv_kfz:int" in args
    # Abgestufte DTV-Leiter (10000/2000/1000) als -j-JSON verdrahtet, Layer-Key `svz`.
    j = args[args.index("-j") + 1]
    assert '"svz"' in j and "10000" in j and "2000" in j and "1000" in j


def test_svz_points_shares_dtv_ladder() -> None:
    # Punkte tragen dieselbe Leiter (YAML-Anchor), aber unter ihrem Layer-Key.
    args = tiles._profile_args(tiles._profiles()["svz_points"])
    j = args[args.index("-j") + 1]
    assert '"svz_points"' in j and "10000" in j and "1000" in j
