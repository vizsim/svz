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
    # Registry = alle status:live aus sources.yaml; jeder Eintrag hat level/name/state.
    sources = load_yaml("sources.yaml")["sources"]
    assert set(registry.REGISTRY) == {c for c, s in sources.items() if s["status"] == "live"}
    for code, src in sources.items():
        for key in ("status", "level", "name", "state", "kind"):
            assert key in src, f"{code}: `{key}` fehlt in sources.yaml"
    assert set(registry.ORDER) <= set(registry.REGISTRY)


def test_every_live_source_has_adapter_module() -> None:
    # YAML <-> Dateisystem: jedes live-Modul ist importierbar und hat normalize().
    import importlib

    for code, module in registry.REGISTRY.items():
        mod = importlib.import_module(module)
        assert callable(getattr(mod, "normalize", None)), f"{code}: {module}.normalize fehlt"
    # Kommunen liegen im Unterpaket adapters/kommunal/.
    for code in registry.by_level("kommune"):
        assert registry.REGISTRY[code].startswith("svzkarte.adapters.kommunal.")
