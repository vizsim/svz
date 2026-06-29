# svzkarte – Pipeline

SVZ-/Verkehrsmengendaten der Bundesländer → kanonisches Schema → FlatGeobuf →
PMTiles (tippecanoe). Aufbau parallel zu `unfallkarte`.

## Konzept

- **Ein kanonisches Schema** ([schema.py](src/svzkarte/schema.py)), auf das *jeder*
  Adapter mappt.
- **Ein Adapter pro Land** unter [adapters/](src/svzkarte/adapters/) mit
  `normalize() -> GeoDataFrame`; gemeinsame Holer (WFS/OGC API/ATOM/ArcGIS/Excel)
  in [adapters/base.py](src/svzkarte/adapters/base.py).
- **Registry** ([registry.py](src/svzkarte/registry.py)): `land-code -> Adapter`.
- Quellen-Metadaten in [config/sources.yaml](config/sources.yaml), Tile-Profil in
  [config/tiles.yaml](config/tiles.yaml).

## CLI

```bash
uv run svz info             # Pfade/Config + Adapter-Status
uv run svz build rp         # ein Land: fetch+normalize -> data/interim/rp.fgb
uv run svz build all        # alle implementierten Länder (fehlertolerant)
uv run svz merge            # alle <land>.fgb -> data/svz/svz_de.fgb (+ validate)
uv run svz tiles            # svz_de.fgb -> data/svz/svz_de.pmtiles
uv run svz manifest         # data/manifest.json
```

## Setup

```bash
uv sync
uv run pytest               # Schema-/Tiles-/Smoke-Tests (ohne Netz)
```

System-Binary (nicht via pip): **tippecanoe**. Ohne installiertes tippecanoe gibt
`svz tiles` das Kommando nur aus (kein Abbruch).

## Status

Implementiert: **RP** (OGC API Features). Geplant (recherchiert in
`../SVZ_Quellen_Bundeslaender.md`): BY, BE, BB, HH, NI, NW, SN, ST, SL, SH, TH, MV,
BW (Excel+Join). HB/HE vorerst zurückgestellt (nur PDF/Viewer → A/B via BASt).
