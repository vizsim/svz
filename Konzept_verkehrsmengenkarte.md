# Konzept: `verkehrsmengenkarte` (SVZ der Bundesländer → PMTiles → MapLibre)

Ziel: SVZ-/Verkehrsmengendaten aller Bundesländer sammeln, per Pipeline laden,
in **ein gemeinsames Format** bringen, als FlatGeobuf zwischenlegen, via tippecanoe
zu PMTiles bauen und mit MapLibre auf einer Karte zeigen. Aufbau bewusst parallel
zu `unfallkarte`, damit Konventionen, Tooling und dein Muskelgedächtnis 1:1 passen.

---

## 1. Grundentscheidung: Adapter + kanonisches Schema

`unfallkarte` hat pro Quelle ein Spezialmodul. Hier sind es 16 Länder + BASt mit
sehr heterogenem Zugang (WFS / OGC API / ATOM / Excel / ArcGIS). Damit das nicht in
16 Sonderlocken ausartet, ist der Kern:

- **ein kanonisches Zielschema** (unten), auf das *jeder* Adapter mappt,
- **ein Adapter pro Land** (`adapters/bw.py`, `by.py`, …), je mit `fetch()` und `normalize() -> GeoDataFrame`,
- eine **Registry** (`land-code → adapter`), analog zu deinem `scenarios/registry.py`,
- gemeinsame **Zugriffs-Bausteine** in `adapters/base.py`, gruppiert nach Zugangsart.

So bleibt jeder Adapter ~30–60 Zeilen: Quelle ziehen + Spalten umbenennen/mappen.
Neue Länder/Jahre = neuer Eintrag, kein Pipeline-Umbau.

---

## 2. Kanonisches Schema (das „halbwegs einheitliche Format")

Eine Zeile = ein Zählstellenbereich (Liniensegment), reprojiziert nach EPSG:4326.

| Feld | Typ | Bedeutung |
|---|---|---|
| `geometry` | LineString/MultiLineString (4326) | Zählstellenbereich; bei reinen Punktquellen Point |
| `dtv_kfz` | int \| null | DTV Kfz gesamt (Kfz/24h) |
| `dtv_sv` | int \| null | DTV Schwerverkehr (Kfz/24h) |
| `sv_anteil` | float \| null | Schwerverkehrsanteil (%) – falls Quelle nur Anteil liefert |
| `metric` | enum `DTV` \| `DTVw` | **Kern gegen Äpfel/Birnen**: alle Tage vs. nur Werktage |
| `year` | int | Bezugsjahr (z.B. 2021) |
| `road_class` | enum `A` \| `B` \| `L` \| `K` \| `G` | Autobahn/Bundes/Landes/Kreis/Gemeinde |
| `road_no` | str \| null | z.B. „B10", „L1187" |
| `station_id` | str \| null | Zählstellennummer der Quelle |
| `state` | str | `BW`, `BY`, … |
| `source` | str | Schlüssel in `sources.yaml` |
| `license` | str | `dl-de/by-2.0`, `dl-de/zero-2.0`, `CC-BY-4.0`, … |

Definiert in `src/svzkarte/schema.py` als Konstantenliste + `validate(gdf)` (Pflicht-
felder vorhanden, `metric`/`road_class` im Enum, CRS == 4326). `normalize()` jedes
Adapters gibt genau diese Spalten zurück; alles andere wird verworfen.

Wichtig: `metric` und `year` werden bis ins PMTile durchgereicht, damit das Frontend
DTV und DTVw nie in dieselbe Farbskala wirft und nach Jahr filtern kann.

---

## 3. Repo-Layout (parallel zu unfallkarte)

```
verkehrsmengenkarte/
├─ pipeline/
│  ├─ pyproject.toml            # uv-Paket "svzkarte", hatchling, ruff, pytest
│  ├─ uv.lock
│  ├─ config/
│  │  ├─ sources.yaml           # je Land: file/label/attribution/date/url (s. §6)
│  │  └─ tiles.yaml             # tippecanoe-Profil(e), s. §5
│  ├─ src/svzkarte/
│  │  ├─ cli.py                 # typer: svz fetch|build|merge|tiles|manifest|deploy
│  │  ├─ config.py              # Paths/Settings/load_yaml (≈ 1:1 von unfallkarte)
│  │  ├─ schema.py              # kanonische Felder + validate()
│  │  ├─ registry.py            # land-code -> adapter
│  │  ├─ merge.py               # alle Länder-fgb -> svz_de.fgb
│  │  ├─ tiles.py               # Tippecanoe-Wrapper (von unfallkarte)
│  │  ├─ manifest.py            # data/manifest.json (Datenstand je Quelle)
│  │  ├─ deploy.py              # b2 sync / Release-Upload
│  │  └─ adapters/
│  │     ├─ base.py             # fetch_wfs/ogc/atom/arcgis, read_excel_zip, to_canonical, write_fgb
│  │     ├─ bw.py by.py be.py bb.py hh.py mv.py ni.py nw.py rp.py sl.py sn.py st.py sh.py th.py …
│  │     └─ bast.py             # Fernstraßen-Backbone (A/B), optional
│  └─ tests/                    # golden-Tests je Adapter (kleiner Ausschnitt)
├─ index.html main.js style.json   # MapLibre-Frontend (Struktur wie unfallkarte)
└─ js/ …                            # addSources.js / addLayers.js / ui / utils
```

Paketname `svzkarte` ist nur ein Vorschlag (analog `unfallkarte`); Reponame frei.
`data/` bleibt gitignored (lokal + Bucket), genau wie bei dir.

---

## 4. CLI & Pipeline-Stufen

```
svz info                 # Pfade/Config-Smoke-Check
svz fetch <land>|all     # Rohdaten -> data/raw/<land>/   (gecacht, --force)
svz build <land>|all     # fetch (falls nötig) -> normalize -> data/interim/<land>.fgb
svz merge                # alle <land>.fgb -> data/svz/svz_de.fgb   (+ validate)
svz tiles                # svz_de.fgb -> data/svz/svz_de.pmtiles    (tippecanoe)
svz manifest             # data/manifest.json (Datenstand/Attribution je Land)
svz deploy               # b2 sync (oder Release-Upload)
```

Datenfluss je Land: **fetch → normalize → `<land>.fgb`**, dann einmal **merge →
`svz_de.fgb`**, dann **tiles → `svz_de.pmtiles`**. Ein einziges Tile-Set mit den
Attributen `state/year/metric/road_class/dtv_kfz` reicht – gefiltert wird im Frontend.

`cli.py` bleibt dünn (lazy import + Aufruf), wie bei dir. Statt 16 Sub-Typer iteriert
ein `build all` über die Registry; `dry_run` für tile-Kommandos übernehmen.

---

## 5. `tiles.yaml` (ein Profil reicht zum Start)

Direkt aus deinem `hvs_lines`/`highways_major`-Muster abgeleitet:

```yaml
profiles:
  svz_lines:
    layer: svz            # Frontend-Vertrag
    minzoom: 6
    maxzoom: 14
    drop_rate: 0
    drop_densest_as_needed: true
    no_feature_limit: true
    no_tile_size_limit: true
```

`tiles.py` kann unverändert aus `unfallkarte` übernommen werden (Profil-Dict →
Flags, `_run` no-op wenn Binary fehlt/`dry_run`).

---

## 6. `sources.yaml` (speist Manifest + Attribution)

Format exakt wie bei dir (`file`/`label`/`attribution`/`date`). Inhalte aus der
bereits erstellten Quellenübersicht. Skizze:

```yaml
datasets:
  svz_de:
    file: "svz/svz_de.pmtiles"
    label: "Verkehrsmengen (SVZ Länder)"
    attribution: "Straßenbauverwaltungen der Länder + BASt (dl-de/by-2.0 u.a.)"
    date: auto            # max(year) über alle gemergten Länder
  # Pro Land Zugangs-Metadaten (vom Adapter genutzt):
  src_by: { kind: wfs,     url: "…BAYSIS…",            year: 2021, license: "CC-BY-4.0" }
  src_be: { kind: wfs,     url: "…gdi.berlin.de…",     year: 2019, license: "dl-de/zero-2.0", metric: DTVw }
  src_ni: { kind: atom,    url: "…strassenbau.ni…",    year: 2021, license: "dl-de/by-2.0" }
  src_rp: { kind: ogcapi,  url: "…geoportal.rlp…/393", year: 2021, license: "dl-de/by-2.0" }
  src_bw: { kind: xlsxzip, url: "…mobidata-bw…",       year: 2024, license: "dl-de/by-2.0", join: zaehlstellen }
  # … sn/st/sl/sh/th/bb/hh/mv analog; he/hb vorerst weglassen
```

`base.py` liest `kind` und wählt den passenden Holer. Die `metric: DTVw`-Ausnahmen
(Berlin, teils Hamburg) stehen hier, damit der Adapter sie korrekt setzt.

---

## 7. Adapter-Bausteine (`adapters/base.py`)

Gruppiert nach den Zugangsarten aus der Recherche:

- `fetch_ogc_features(url, collection)` – RLP (`spatial-objects/393`), moderne ldproxy-Endpunkte.
- `fetch_wfs(url, typename, bbox?)` – BY, SN, ST-Netz, SL, TH, BB, SH (GetFeature → GeoJSON/GML).
- `fetch_atom(feed_url)` – NI und andere INSPIRE-Downloaddienste (Atom → verlinkte GML/Shape).
- `fetch_arcgis_paginated(query_url, out_fields)` – **direkt aus deiner `hvs.py`** wiederverwendbar (BASt-/ArcGIS-artige Dienste, `resultOffset`-Pagination, `outSR=4326`).
- `read_excel_zip(url) -> DataFrame` + `join_stations(df, stations_gdf, on="station_id")` – der BW-Sonderfall (Werte tabellarisch, Geometrie aus der Zählstellen-Karte).
- `to_canonical(gdf, mapping, *, metric, year, road_class, state, source, license)` – benennt um, setzt Konstanten, wirft Fremdspalten weg, reprojiziert nach 4326.
- `write_fgb(gdf, path)` – `to_file(driver="FlatGeobuf")`, vorher Null/empty-Geometrien filtern (genau die Falle aus deiner `hvs.to_fgb`).

Ein Land-Adapter ist dann nur noch Verdrahtung, z.B. RLP:

```python
def normalize() -> "GeoDataFrame":
    src = base.fetch_ogc_features(cfg["url"], "SVZ2021_Zaehlstellenbereiche")
    return base.to_canonical(
        src, mapping={"DTV": "dtv_kfz", "DTV_SV": "dtv_sv", "strasse": "road_no"},
        metric="DTV", year=2021, road_class_from="klasse",
        state="RP", source="src_rp", license="dl-de/by-2.0",
    )
```

---

## 8. Frontend (MapLibre, Struktur wie unfallkarte)

Statische App im Repo-Root. PMTiles via `pmtiles`-Protokoll, `addSources.js`
registriert eine Source `svz` (→ `svz_de.pmtiles`), `addLayers.js` einen
Linien-Layer. Einfärbung über `dtv_kfz` (Step/Interpolate), Liniendicke optional
nach Klasse. Filter-UI (analog `setupLayerToggles`): **Jahr**, **Bundesland**,
**Straßenklasse**, **Metrik (DTV/DTVw getrennt!)**. Popup zeigt
`road_no · dtv_kfz · year · state · source`. Attribution-Control wird wie bei dir
aus dem Manifest zusammengesetzt (`applyDataVintages.js`-Muster → „Datenstand je Land").

---

## 9. CI / Ausspielung (GitHub Actions)

Workflow `build.yml`, `workflow_dispatch` + monatlicher Cron:

1. `astral-sh/setup-uv`, dann `uv sync`.
2. tippecanoe bereitstellen (apt-Paket oder `make` aus Quelle; ggf. als gecachtes Artefakt).
3. `uv run svz build all && uv run svz merge && uv run svz tiles`.
4. `uv run svz manifest`.
5. Ausspielen: entweder **B2** wie unfallkarte (`b2 sync`, Keys als GH-Secrets), oder
   – kostenlos – `svz_de.pmtiles` als **GitHub-Release-Asset** + Frontend auf **GitHub Pages**.
   PMTiles ist Range-Request-fähig, also als eine Datei direkt bedienbar (ein Range-fähiger
   Host wie B2/R2/Cloudflare ist empfehlenswert; reine Pages-Auslieferung vorher testen).

Fehlertoleranz: ein Land-Adapter, der fehlschlägt (Dienst down), darf den Gesamt-
Build nicht killen – `build all` sammelt Fehler, baut `merge` aus dem, was da ist,
und meldet die Lücken (wie deine OBS-Portal-Skips).

---

## 10. Rollout in Phasen

- **Phase 0** – Gerüst: Paket, `config.py`, `schema.py`, `tiles.py`, leere Registry, `info`.
- **Phase 1** – die sauberen Dienste zuerst: BE, BY, BB, HH, NI, RP, SN, SL, TH, SH (+ ST/Netz). Ein Adapter, dann das Muster kopieren.
- **Phase 1b** – BW (Excel + Join auf Zählstellen-Geometrie).
- **Phase 2** – Frontend-Polish (Filter, Legende, Attribution), CI/Deploy.
- **Später** – HB (PDF) und HE (UIG-Anfrage) ergänzen; BASt-Backbone für lückenlose A/B; SVZ 2025, sobald ab Ende 2026 verfügbar.

---

## 11. Stolpersteine (in den Build eingebaut)

- **CRS**: Quellen in UTM 32N/33N → konsequent nach 4326 reprojizieren (`to_canonical`).
- **DTV ≠ DTVw**: nie zusammen einfärben; `metric` ist Pflichtattribut und Filter.
- **Jahre gemischt**: `year` mitführen; Default-Filter auf neuestes Jahr je Land.
- **Geometrietyp**: manche Quellen liefern Punkte/Zählstellen statt Linien → `geom_kind`-Marker optional, Frontend rendert beides.
- **Lizenzpflege**: `license` je Zeile + Attribution-Aggregat im Manifest (zero/by/CC-BY auseinanderhalten).
- **Null/empty-Geometrien** vor dem FGB-Write filtern (deine `hvs`-Erfahrung).
