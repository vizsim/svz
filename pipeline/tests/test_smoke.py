"""Smoke: Paket importiert, Pfade/Config-Wiring steht, Registry konsistent."""

from __future__ import annotations

from svzkarte import __version__, registry
from svzkarte.config import get_paths, load_yaml


def test_version_and_paths() -> None:
    assert __version__
    paths = get_paths()
    assert paths.config.name == "config"
    assert paths.interim_fgb("rp").name == "rp.fgb"


def test_registry_and_sources_consistent() -> None:
    # Jedes implementierte Land hat einen sources.yaml-Eintrag.
    sources = load_yaml("sources.yaml")["sources"]
    for code in registry.REGISTRY:
        assert code in sources, f"{code} fehlt in sources.yaml"
    # ORDER referenziert nur implementierte Länder.
    assert set(registry.ORDER) <= set(registry.REGISTRY)
