# svzkarte – Pipeline

SVZ-/Verkehrsmengendaten der Länder und des Bundes (BASt) sowie – begrifflich getrennt,
keine SVZ – kommunale Verkehrszählungen einzelner Städte → kanonisches Schema →
FlatGeobuf (je Ebene) → PMTiles (tippecanoe). Aufbau parallel zu `unfallkarte`.

## Konzept

- **Ein kanonisches Schema** ([schema.py](src/svzkarte/schema.py)), auf das *jeder*
  Adapter mappt. `level` (bund/land/kommune) = Herausgeber-Ebene, `source` = Schlüssel
  in sources.yaml (Filter im Frontend), `metric` DTV/DTVw/**24h** (Einzelzählung).
- **Ein Adapter pro Quelle** unter [adapters/](src/svzkarte/adapters/) (Länder/Bund)
  bzw. [adapters/kommunal/](src/svzkarte/adapters/kommunal/) (Städte), jeweils
  `normalize() -> GeoDataFrame`; gemeinsame Holer (WFS/OGC API/ATOM/ZIP/ArcGIS/Excel)
  in [adapters/base.py](src/svzkarte/adapters/base.py).
- **[config/sources.yaml](config/sources.yaml) ist die einzige Quellenliste**: die
  Registry ([registry.py](src/svzkarte/registry.py)) leitet `status: live` → Adapter-Modul
  daraus ab, `svz manifest` schreibt sie (inkl. BBox/Featurezahl) nach
  `data/manifest.json`, woraus der Viewer sein Quellen-Panel baut.
- **Merge je Ebene × Geometrie** ([merge.py](src/svzkarte/merge.py)) → drei PMTiles
  ([tiles.py](src/svzkarte/tiles.py), Profile in [config/tiles.yaml](config/tiles.yaml)):
  `svz_de` (Länder), `svz_bast` (Bund), `svz_kommunal` (Kommunen, ab Zoom 8).
- **Generische Portal-Adapter**: ein Modul mit `normalize(code)` für viele Quellen im
  selben Format (z.B. `kommunal/mobidata_bw.py`); in sources.yaml per `adapter:` referenziert.
- Konzept der Kommunen-Ebene: [../docs/Konzept_kommunale_daten.md](../docs/Konzept_kommunale_daten.md);
  Quellensuche und Verarbeitungsmuster: [../AGENTS.md](../AGENTS.md).

## CLI

```bash
uv run svz info                     # Pfade/Config + live-Quellen je Ebene
uv run svz build by                 # eine Quelle: fetch+normalize -> data/interim/by.fgb
uv run svz build ravensburg         # Kommune genauso (Code aus sources.yaml)
uv run svz build all                # alle live-Quellen (fehlertolerant)
uv run svz merge                    # interim/*.fgb -> data/svz/ je Ebene (+ validate)
uv run svz tiles                    # alle drei PMTiles
uv run svz tiles --only svz_kommunal   # nur die Kommunen neu kacheln (Sekunden)
uv run svz manifest                 # data/manifest.json (Datensätze + Quellenliste fürs Frontend)
```

## Neue Quelle (Land oder Stadt)

1. Eintrag in `config/sources.yaml` (`status: live`, `level`, `name`, `state`, `kind`,
   `url`, `year`, `license`, `metric`, `access`).
2. Adapter `adapters/<code>.py` bzw. `adapters/kommunal/<code>.py` mit `normalize()`
   (Holer aus `base`, dann `base.to_canonical(...)`; Jahr je Feature via `year_from`).
3. Golden-Test `tests/test_<code>.py` (Holer monkeypatchen, `schema.validate`).
4. `svz build <code>`, `svz merge`, `svz tiles --only …`, `svz manifest`; README-Zeile.

## Setup

```bash
uv sync
uv run pytest               # Schema-/Merge-/Tiles-/Adapter-Golden-Tests (ohne Netz)
```

System-Binary (nicht via pip): **tippecanoe** (+ `tile-join`). Ohne installiertes
tippecanoe gibt `svz tiles` das Kommando nur aus (kein Abbruch).

## Status

Live: **11 Länder** (BE, NI, BY, BB, HH, NW, TH, SN, ST als Linien; BW, SL als Punkte),
**BASt-Backbone** (A+B, Punkte), **Kommunen: Köln, Düsseldorf, Frankfurt am Main**
(Linien; Frankfurt als 24h-Mittel) und **Ravensburg, Weingarten, Berg, Baienfurt, Baindt**
(Punkte, 24h, generischer MobiData-BW-Adapter). Offen: RP (OGC API defekt), HB/HE/MV/SH
(kein maschinenlesbarer DTV) – Details in [../docs/TODO.md](../docs/TODO.md).
