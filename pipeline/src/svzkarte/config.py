"""Zentrale Konfiguration: Pfade, .env-Secrets und YAML-Configs.

Eine Quelle der Wahrheit für: wo liegen Daten, wie heißen Buckets/Secrets, und
welche deklarativen Configs (sources/tiles) gibt es. Pipeline-Module importieren
von hier statt Pfade/ENV selbst zu raten. 1:1-Muster aus `unfallkarte`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


def repo_root() -> Path:
    """Repo-Wurzel: .../src/svzkarte/config.py -> parents[2]."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    """Kanonische Pfade. `data/` ist gitignored (lokal + Bucket, nicht im Git)."""

    root: Path

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def raw(self) -> Path:
        return self.data / "raw"  # Rohdownloads je Land: data/raw/<land>/

    @property
    def interim(self) -> Path:
        return self.data / "interim"  # je Land normalisiert: data/interim/<land>.fgb

    @property
    def svz(self) -> Path:
        return self.data / "svz"  # gemergte svz_de.fgb + svz_de.pmtiles

    def raw_land(self, land: str) -> Path:
        return self.raw / land

    def interim_fgb(self, land: str) -> Path:
        return self.interim / f"{land}.fgb"

    def ensure(self) -> None:
        for p in (self.data, self.raw, self.interim, self.svz):
            p.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Secrets/Env aus `.env`. Niemals committen. (Deploy-Ziel noch offen.)"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = "svzkarte-data"


@lru_cache
def get_paths() -> Paths:
    return Paths(root=repo_root())


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml(name: str) -> dict[str, Any]:
    """Lädt config/<name> (z.B. 'sources.yaml')."""
    path = get_paths().config / name
    if not path.exists():
        raise FileNotFoundError(f"Config fehlt: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Config {name} ist kein Mapping")
    return data
