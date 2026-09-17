# AGENTS.md – Datenquellen finden, einordnen, verarbeiten

Erfahrungswissen aus dem Aufbau dieser Karte (Länder-SVZ, BASt, Kommunen, Regionen) für
alle, die neue Quellen anschließen – Menschen wie Agenten. Ergänzt
[README.md](README.md) (Stand/Tabellen), [pipeline/README.md](pipeline/README.md)
(CLI/Ablauf) und [docs/Konzept_kommunale_daten.md](docs/Konzept_kommunale_daten.md)
(Ebenen-Konzept). Sprache: Deutsch, Code-Kommentare ebenso.

## 1. Begriffe, die das Wording bestimmen

- **SVZ** = amtliche Straßenverkehrszählung (Bund/BASt + Straßenbauverwaltungen der
  Länder, ~5-Jahres-Turnus, Ergebnis DTV/DTVw als Jahresmittel). Nur diese Daten heißen
  im Projekt „SVZ".
- **Kommunale Verkehrszählungen** = eigene Erhebungen der Städte (Knotenpunktzählungen,
  Dauerzählstellen, projektbezogen). **Keine SVZ.** Eigene Ebene `kommune`, im Panel
  „Kommunen (eigene Zählungen)".
- **Abgeleitete Datensätze** (z.B. DiSTILL Lausitz: SVZ-Werte der Länder auf OSM-Ways,
  mit Spuren/Auslastung) sind keine eigene Quelle. **Vor dem Anschluss per
  Zählstellennummer gegen bb/sn/… prüfen, ob neue Werte dazukommen** – bei der Lausitz
  waren alle 371 Zählstellen mit identischem DTV schon da → verworfen.
- **Metriken**: `DTV` (alle Tage), `DTVw` (werktags), `24h` (Einzelzählung an einem
  Werktag – kein Mittel). Eine 16h-Zählung, die die Stadt selbst auf 24h hochrechnet und
  „DTVa" nennt (Düsseldorf), ist `DTV`; eine einzelne Di/Do-Zählung (Ravensburg) ist `24h`.
  Auch ein **Mittel weniger Werktagszählungen ohne Hochrechnung aufs Jahr** (Frankfurt:
  „Mittelwerte 2019–2023", Zähltage nur Di–Do) bleibt `24h` – die Wochentage von
  `zaehldatum` auszählen verrät, was man vor sich hat.

## 2. Wo man Quellen findet (Reihenfolge, die sich bewährt hat)

1. **GovData CKAN-API** – aggregiert Mobilithek, Open.NRW, Open Data BW/BB/Hessen,
   Transparenzportal HH u.v.m. Ein Sweep mit `package_search` über
   `Verkehrszählung Kfz`, `Verkehrsmengen`, `"Verkehrszähldaten"`, `Zählstellen DTV`,
   `<Stadt> Verkehrszählung` liefert in Minuten, was es bundesweit gibt:
   `https://www.govdata.de/ckan/api/3/action/package_search?q=…&rows=60`.
   Danach `package_search` mit dem exakten Titel in Anführungszeichen für Ressourcen-URLs.
2. **Landes-Mobilitätsportale**: MobiData BW (CKAN, Gruppe `verkehrszaehldaten` – dort
   veröffentlichen kleine Kommunen im selben Excel-Format), Open.NRW, opendata.dresden.de
   (eigenes Portal, oft 503), open.bydata (piveau, keine CKAN-API).
3. **Städtische Portale direkt**: viele sind CKAN (`/api/3/action/package_search`), einige
   DKAN (Düsseldorf: Ressourcen-Seiten statt Dateien, DCAT-Export unter
   `/dcatapde/dataset/<name>.json`), einige Opendatasoft (Potsdam, Mannheim, Dortmund:
   `/api/explore/v2.1/catalog/datasets?limit=100`, dann Titel filtern; `select=`/`where=`
   liefern schnell 400). Viele APIs sind 404 oder liefern HTML – erst prüfen, dann parsen.
4. **Mobilithek**: Dateien unter `mobilithek.info/mdp-api/files/aux/<id>/<datei>` laden nur
   mit Browser-User-Agent + `Accept: application/octet-stream`; ohne kommt eine HTML-Shell.
   Angebotsseiten (`/offers/<id>`) sind reines JS – Lizenz von Hand nachschlagen.
5. **Suchbegriffe**: *SVZ, Straßenverkehrszählung, Verkehrsmengen(karte), Verkehrsstärke,
   Verkehrsbelastung, Zählstellen, Zählstellenbereiche, Verkehrszähldaten, Knotenpunktzählung,
   DTV, Kfz/24h*. Rad-Zählstellen (Eco-Counter) tauchen bei allen Suchen mit auf – aussortieren.

## 3. Quellentypen und wie man sie liest

| Typ | Beispiele | Holer in `base.py` | Fallen |
|---|---|---|---|
| WFS deegree/GeoServer (JSON) | BE, HH, Düsseldorf | `fetch_wfs(output_format="application/json")` | `typeName` (1.x) vs. `typeNames` (2.0) – `fetch_wfs` wählt nach Version |
| WFS ArcGIS Server | BY, SL | `fetch_wfs(output_format="GEOJSON")` | EPSG:4326 liefert lat,lon → `srs="CRS:84"` |
| WFS nur GML, altes Profil | BB, TH (nur 1.1.0!) | `fetch_wfs(output_format=None, src_crs=…)` | native CRS anfordern, Achsenfalle bei 4326 |
| WFS ohne Werte (nur Netz) | ST, SH | Netz × Werte-Excel über Netzknoten `(vnk,nnk)` | Join-Schlüssel als String normalisieren |
| OGC API Features | RP (defekt) | `fetch_ogc_features` | Backend-Fehler → `status: research` |
| Shapefile-ZIP (INSPIRE/Atom) | NI, NW, SN | `fetch_zip` / `fetch_atom` | ganzes ZIP an GDAL geben (Sidecars) |
| Shapefile-ZIP mit mehreren Layern | Köln (VISUM link/node) | `fetch_zip(layer=…)` | DBF kürzt Spaltennamen (`R_K_2016~2`) → Regex |
| ZIP mit mehreren GeoJSONs | Mobilithek-Pakete (z.B. DiSTILL Lausitz) | `fetch_zip(member=…, headers=…)` | `zip://…!datei.json`; Browser-UA nötig |
| GeoJSON direkt | Düsseldorf 2019 | `fetch_geojson` | – |
| CSV mit Koordinaten | BW (`gpsx1`/`gpsy1`) | `fetch_csv_points(x=, y=)` | alles als String lesen (Zählstellennummern!); Standdatum im Dateinamen → URL stirbt beim nächsten Update |
| Excel mit Koordinaten | BASt, MobiData-Kommunen | `read_excel_zip(sheet=)` + `points_from_xy` | Zahlen als Strings/Leerstrings → `to_numeric(errors="coerce")` |
| Excel/CSV ohne Geometrie | ST-Werte, Stuttgart-Kordon | Join auf Netz; ohne Schlüssel unbrauchbar | Stuttgart: nur Messpunkt-Kategorie, keine Koordinaten |
| Nur PDF/Viewer/WMS | HB, HE, MV, Münster, Potsdam, Dortmund (Werte auf Anfrage) | – | `status: blocked`, Sackgasse dokumentieren |
| DATEX II / Echtzeit-Zähler | Konstanz, Gelsenkirchen, Ettlingen | – | Stunden-/Live-Werte, kein DTV → nicht Ziel dieser Karte |

## 4. Verarbeitungsmuster (was sich wiederholt)

- **Alles landet in `base.to_canonical`**: Spalten-Mapping, Konstanten, Reprojektion,
  Fremdspalten weg. `year_from=` statt `year=`, sobald Jahre je Feature variieren.
  `level` kommt automatisch aus `sources.yaml` über `source`.
- **0 heißt „nicht gezählt", nicht „kein Verkehr"** (Issue #2): fast jede Quelle füllt
  Abschnitte ohne Zählwert mit 0 (NW allein 1.228). `base.normalize_counts` (in
  `to_canonical` und beim `merge` älterer interim-FGB) macht aus `dtv_kfz = 0` leer → die
  Karte zeigt grau „keine Angabe". `dtv_sv = 0` bleibt nur neben einem echten Kfz-Wert.
  Bei neuen Quellen prüfen: klafft zwischen 0 und dem kleinsten echten Wert eine Lücke?
- **Jüngste Zählung je Zählstelle** (MobiData-Excel mit Zählblöcken `KFZ_n/DATUM_n`):
  Blöcke in lange Tabelle, numerisch erzwingen, `sort_values(datum).groupby(id).tail(1)`.
- **Richtungswerte** (Köln `K_<Jahr>` / `R_K_<Jahr>`): jüngstes Jahr mit beiden Richtungen
  summieren, sonst jüngstes Jahr mit einer; Kanten ohne Werte fallen weg.
- **Mehrere Layer je Fahrzeugart** (Düsseldorf): UUIDs je Layer verschieden, Geometrie
  identisch → Join über `geometry.wkb`; SV = Lkw oA + Lkw mA + Bus. Gibt es eine gemeinsame
  Abschnittsnummer (Frankfurt `str_nr`), darüber joinen – dort ist die Digitalisierrichtung
  zwischen den Layern teils gedreht, ein WKB-Join würde diese Abschnitte verlieren.
- **Dopplung prüfen, bevor man baut**: `station_id`-Mengen und DTV-Werte eines neuen
  Datensatzes gegen die schon integrierten Quellen im selben Gebiet vergleichen
  (`merge` auf `station_id`, Anteil identischer Werte). Identisch → nicht anschließen.
- **Straßenklasse aus dem Namen**, wenn die Quelle keine hat: Regex `^[ABLK]\s?\d+` auf
  Namens-Tokens („B32_Ulmerstraße", „Autobahn A46"); Rest `G` (Gemeinde-/Stadtstraße).
- **Golden-Test je Adapter**: Holer aus `base` monkeypatchen, 2–4 Fälle, die genau die
  Regeln oben fixieren, `schema.validate` drüber. Kein Netz im Test.
- **Generische Portal-Adapter** (`normalize(code)`, in YAML `adapter:` setzen): ein Modul
  für alle Quellen im selben Format (MobiData-BW-Excel). Die Registry bindet den Code.

## 5. Live-Verifikation vor dem Adapter (immer)

1. `GetCapabilities` + `DescribeFeatureType` (Versionen, Formate, Felder, CRS).
2. Ein `GetFeature` mit `maxFeatures=3` (bzw. Datei laden) und **in geopandas öffnen**:
   Anzahl, CRS, Geometrietyp, `total_bounds` (liegt es dort, wo es soll?), `describe()`
   der Wertspalten (Nullen? Ausreißer? Strings?).
3. **Lizenz** aus Capabilities (`Fees/AccessConstraints`), CKAN `license_id`, DCAT-Export
   oder INSPIRE-Metadatensatz. Unklar → im YAML als „unbekannt"/„lt. Portal" markieren
   und im README nennen, nicht raten.
4. Erst dann Adapter + Test; dann `svz build <code>`, `svz merge`,
   `svz tiles --only <datensatz>`, `svz manifest`, Screenshot als Nachweis.

## 6. Bekannte Sackgassen (nicht nochmal suchen)

- **`research`-Dienste wiederbeleben sich**: Frankfurts WFS lieferte monatelang auf jedes
  GetFeature 500 und lief im Sept. 2026 plötzlich → vor jedem Sweep die `research`-Einträge
  in `sources.yaml` kurz neu testen. Portale hinter Bot-Schutz (opendata.hessen.de: Anubis)
  nicht aushebeln – Lizenz/Beschreibung stehen gespiegelt in der GovData-CKAN-API.
- **Münster**: ZIP mit einer PDF/XLS je Zählung (Spitzenstunden), kein Tageswert je Stelle.
- **Potsdam**: nur Knotenstandorte + PDF-ZIP je Knoten. **Dortmund**: nur Zählstellenplan,
  Werte kostenpflichtig auf Anfrage. **Stuttgart**: Kordon-Summen ohne Koordinaten.
- **Dresden**: Themenstadtplan-Thema `STA_VERKEHRSMENGEN` (Layer L1204–L1206) existiert,
  WFS-NodeId dazu nicht gefunden; Open-Data-Portal häufig 503.
- **Konstanz/Mannheim/Leipzig/Heidelberg/Aachen**: nur Rad-Zähler bzw. Echtzeit.
- **Lausitz (DiSTILL, Mobilithek 983406200238284800)**: SVZ 2021 BB+SN auf OSM-Ways –
  identische Werte wie `bb`/`sn`, kein Mehrwert (Lizenz zudem nur per JS einsehbar).
- **Bund**: BASt-Excel deckt A+B bundesweit; Länder liefern A seit 2021 teils nicht mehr.

## 7. Technische Stolpersteine

- tippecanoe schreibt FlatGeobuf-Zahlen als Strings → `attribute_types` in `tiles.yaml`.
- FlatGeobuf hält nur einen Geometrietyp und keine Null-Geometrien → merge trennt
  Linien/Punkte, `write_fgb` filtert.
- Doppelt kodierte URLs (`%2520`) sind manchmal die echten Dateinamen (Köln).
- `pkill -f` mit dem eigenen Kommandotext killt die Shell; Range-Server per PID beenden.
- Screenshots nur per CDP mit Warten auf `map.areTilesLoaded()` – s. `docs/cdp_shot.py`.
