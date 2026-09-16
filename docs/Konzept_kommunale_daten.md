# Konzept: Kommunale Verkehrszählungen als dritte Ebene

Bezug: [Issue #1 „Kommunale Daten ergänzen?"](https://github.com/vizsim/svz/issues/1)
(Beispiel Ravensburg). Stand: September 2026, Branch `feature/kommunale-daten`.
Umgesetzt für zwei Pilotquellen: **Ravensburg** (Punkte, 24h-Einzelzählungen) und
**Köln** (Linien, DTVw auf Netzkanten). Was hier als „umgesetzt" steht, ist im Branch
drin; „Option" = Vorschlag, noch nicht gebaut.

## 0. Begriffe: SVZ ≠ kommunale Zählung

**SVZ** (Straßenverkehrszählung) ist die amtliche, bundesweit abgestimmte Zählung auf
Bundesfernstraßen und dem Landes-/Kreisnetz (BASt-Methodik, ~5-Jahres-Turnus, Ergebnis
DTV/DTVw als Jahresmittel) – Herausgeber sind Bund (BASt) und die Straßenbauverwaltungen
der Länder. **Kommunale Verkehrszählungen** sind davon getrennt: die Städte zählen
selbst (Knotenpunktzählungen, Dauerzählstellen, projektbezogene Erhebungen), mit eigener
Methodik und ohne diesen Turnus. Sie sind **keine SVZ-Daten** und werden im Projekt
überall so benannt: im Titel („SVZ der Länder + kommunale Zählungen"), im Panel
(„Kommunen (eigene Zählungen)" vs. „Länder (SVZ)" / „Bund (BASt)"), in README und
Attribution. Der Dateiname `svz_kommunal.pmtiles` folgt nur dem Projekt-Präfix `svz_`
(Paketname), nicht der Datenherkunft.

## 1. Was kommunale Daten anders macht

Länder-SVZ und BASt sind methodisch verwandt (Zählstellen(-bereiche), DTV/DTVw,
Straßenklasse, ein Bezugsjahr je Quelle). Kommunale Zählungen brechen fast jede dieser
Annahmen:

| Aspekt | Länder / BASt | Kommunen (Ravensburg, Köln, typisch) |
|---|---|---|
| Metrik | DTV / DTVw (Jahresmittel) | oft **Einzelzählung 24 h an einem Werktag** (Ravensburg), teils hochgerechnete DTVw (Köln) |
| Bezugsjahr | eines je Quelle | **je Zählstelle verschieden** (Ravensburg 2023–2026, Köln 2016–2019) |
| Geometrie | Zählstellenbereiche (Linien) oder Zählstellen (Punkte) | Knotenpunkte (Punkte) **oder** Netzkanten (Linien), je Stadt |
| Straßenklasse | A/B/L/K | meist **keine** – städtisches Netz („Gemeinde-/Stadtstraße") |
| Identität | Straßennummer + Zählstellennr. | **Straßen-/Knotenname** ist der eigentliche Schlüssel |
| Ausdehnung | Land | ein Stadtgebiet – auf Deutschland-Zoom ein Punkt |
| Zusatzwerte | Kfz, SV | oft auch **Rad, Fußgänger** (Ravensburg), Richtungswerte (Köln) |
| Format | WFS/ZIP/GeoJSON/Excel | Excel-Übersichten, VISUM-Shape-Exporte, CSV, PDF |
| Anzahl | 16 + 1 | potenziell **Dutzende bis Hunderte** Städte |

Daraus folgen die drei Entscheidungen des Konzepts: eigene **Ebene** mit eigenem
PMTiles, **Schema-Erweiterung** statt Umdeutung bestehender Felder, und ein Frontend,
das nicht mehr „pro Land" denkt, sondern „pro Quelle innerhalb einer Ebene".

## 2. Zielbild: drei Ebenen, drei PMTiles, ein Schema

```text
level    Quelle(n)                   FGB (merge)                        PMTiles (tiles)          Layer
bund     bast                         svz_bast.fgb                       svz_bast.pmtiles         bast
land     be, by, bb, hh, ni, nw, …    svz_lines.fgb + svz_points.fgb     svz_de.pmtiles           svz, svz_points
kommune  koeln, ravensburg, …         kommunal_lines.fgb + …_points.fgb  svz_kommunal.pmtiles     kommunal, kommunal_points
```

Warum ein **eigenes PMTiles** für Kommunen (statt sie in `svz_de` zu mischen):

- **Mindest-Zoom 8** ([tiles.yaml](../pipeline/config/tiles.yaml)): dichte Innenstadtnetze
  würden die kleinen Zooms aufblähen, ohne dort sichtbar zu sein. Die Länder behalten
  ihre DTV-Leiter ab Zoom 5.
- **Unabhängiger Rebuild/Deploy**: eine neue Stadt kachelt in Sekunden
  (`svz tiles --only svz_kommunal`), ohne 56 MB Länder-Tiles neu zu erzeugen.
- **Überlappung schaltbar**: Köln liegt über den NRW-Linien (B/L/K), mit anderer Metrik
  (DTVw 2016–19 vs. DTV 2019). Als eigene Ebene lässt sich das ein-/ausblenden wie der
  BASt-Backbone.
- Spiegelt die Herausgeber-Struktur (Bund / Land / Kommune) 1:1 – das ist auch die
  Gliederung, die Nutzer im Panel wiedererkennen.

### 2b. Abgeleitete regionale Datensätze – geprüft und verworfen

Beim Suchen nach Kommunen tauchte ein Typ auf, der in keine der drei Ebenen passt:
**regionale Auswertungen, die die SVZ-Werte der Länder auf ein anderes Netz legen** –
die DiSTILL-Daten der IPG Lausitz (SVZ 2021 BB+SN auf OSM-Ways, mit Fahrstreifen und
Auslastungsgrad). Ein Testlauf als eigene Ebene `region` zeigte: alle 371 Zählstellen
sind mit **identischem DTV** bereits in den Landesdaten von BB und SN, keine einzige
kommt hinzu; neu sind nur die OSM-Geometrie und Zusatzgrößen, die das Schema nicht
abbildet. Ergebnis: wieder ausgebaut. **Regel daraus:** Vor dem Anschluss eines
abgeleiteten Datensatzes per Zählstellennummer gegen die vorhandenen Quellen prüfen, ob
er überhaupt neue Werte bringt (s. [AGENTS.md](../AGENTS.md)).

## 3. Pipeline-Struktur (umgesetzt)

### 3.1 `sources.yaml` ist die einzige Quellenliste

Bisher war jede Quelle an **vier** Stellen zu pflegen (`sources.yaml`,
`registry.REGISTRY` + `ORDER`, `main.js`-`SOURCES`, README-Tabelle). Bei Dutzenden
Städten hält das niemand konsistent. Jetzt:

- [`sources.yaml`](../pipeline/config/sources.yaml) trägt je Quelle **`level`**,
  **`name`**, **`state`**, `status`, `kind`, `year`, `metric`, `license`, **`access`**
  (Format-Label + URL für die Zugangs-Spalte), bei Kommunen `ags` und `portal`.
- [`registry.py`](../pipeline/src/svzkarte/registry.py) **leitet sich daraus ab**:
  alle `status: live` → Adapter-Modul per Konvention (`adapters/<code>.py` bzw.
  `adapters/kommunal/<code>.py`; `adapter:` überschreibt). Build-Reihenfolge =
  YAML-Reihenfolge. Ein Test prüft, dass jedes live-Modul importierbar ist.
- [`manifest.py`](../pipeline/src/svzkarte/manifest.py) schreibt die Quellenliste
  inkl. **`bbox`** und Featurezahl (aus den interim-FGB via `pyogrio.read_info`) nach
  `data/manifest.json` – **das Frontend baut sein Panel daraus**.
- Bleibt von Hand: die README-Tabellen (Doku). Option: `svz manifest --readme` erzeugt
  die Tabellen aus der YAML.

**Neue Quelle hinzufügen** = 1) YAML-Eintrag, 2) Adapter-Datei, 3) Golden-Test,
4) `svz build <code> && svz merge && svz tiles --only … && svz manifest`. README-Zeile
ergänzen. Nichts in `main.js`.

### 3.2 Schema-Erweiterungen ([schema.py](../pipeline/src/svzkarte/schema.py))

| Feld | Änderung | Grund |
|---|---|---|
| `level` | **neu, Pflicht**: `bund` / `land` / `kommune` | steuert merge → PMTiles; selbstbeschreibende Features |
| `name` | **neu, optional**: Straßen-/Knotenname lt. Quelle | kommunal ist der Name der Schlüssel („Eywiesenstraße / Gartenstraße"), Popup-Titel |
| `metric` | **`24h`** neu neben DTV/DTVw | 24h-Einzelzählung an einem Werktag ist **kein** DTV und darf nicht so heißen |
| `year` | je Feature statt Konstante (`to_canonical(year_from=…)`) | Ravensburg/Köln mischen Zähljahre |
| `road_class` | unverändert; `G` heißt jetzt „Gemeinde-/Stadtstraße bzw. Klasse lt. Quelle offen" | Kommunen liefern keine Klasse; wo der Name eine Nummer trägt (Ravensburg „B32_…"), wird sie erkannt |
| `state` | unverändert; bei Kommunen das Bundesland der Stadt | Gruppierung/Anzeige, kein Filter mehr |
| `source` | unverändert, jetzt **der** Filter-Schlüssel im Frontend | ein Schlüssel für Länder, Kommunen und BASt gleichermaßen |

`to_canonical` liest `level` automatisch aus `sources.yaml` (über `source`), bestehende
Adapter blieben unverändert. `merge` rüstet ältere interim-FGB (ohne `level`/`name`)
nach, damit kein voller Rebuild aller Länder nötig war.

### 3.3 Adapter-Konvention `adapters/kommunal/`

Eigenes Unterpaket, gleiche Bausteine aus `base.py`. Die zwei Piloten decken die zwei
typischen Muster ab:

- **Ravensburg** ([ravensburg.py](../pipeline/src/svzkarte/adapters/kommunal/ravensburg.py)):
  Übersichts-Excel, je Zählstelle bis zu vier Zählungen als wiederholte Spaltenblöcke
  `KFZ_n/RAD_n/FUSSGAENGER_n/SV_n/DATUM_n` → lange Tabelle → **jüngste Zählung je
  Zählstelle** → Punkte (WGS84). Metrik `24h`. Straßennummer/-klasse aus dem Namen.
- **Köln** ([koeln.py](../pipeline/src/svzkarte/adapters/kommunal/koeln.py)):
  VISUM-Netzexport (Shapefile, 22.988 Kanten, DHDN/GK2), Werte **je Richtung und Jahr**
  (`K_2019_24H`, `R_K_2019~5`). Regel: jüngstes Jahr mit **beiden** Richtungen
  (Summe = Querschnitt), sonst jüngstes Jahr mit einer Richtung; Kanten ohne Werte
  entfallen (2.551 bleiben). Metrik DTVw, `road_class` G, `name` = Straßenname.

Beide haben Offline-Golden-Tests (monkeypatch der Holer) wie die Länder.

Zweite Runde (5 weitere Quellen) brachte zwei weitere Muster:

- **Generischer Portal-Adapter** ([mobidata_bw.py](../pipeline/src/svzkarte/adapters/kommunal/mobidata_bw.py)):
  MobiData BW verteilt für Ravensburg, Weingarten, Berg, Baienfurt und Baindt dasselbe
  Excel-Format. Ein Modul mit `normalize(code)`, in `sources.yaml` per `adapter:`
  referenziert; die Registry bindet den Quellen-Code. Neue Kommune = ein YAML-Eintrag.
- **Ein WFS-Layer je Fahrzeugart** ([duesseldorf.py](../pipeline/src/svzkarte/adapters/kommunal/duesseldorf.py)):
  Kfz, Lkw oA/mA, Bus als getrennte Layer mit eigenen UUIDs, aber identischer Geometrie
  → Join über `geometry.wkb`; 5-Jahres-Mittel vor 10-Jahres-Mittel, Endjahr je Feature.

## 4. Frontend / UI (umgesetzt)

Leitfrage aus dem Issue: **Wie behält man die Übersicht**, wenn zu 11 Ländern
Dutzende Städte kommen?

1. **Panel nach Ebenen gruppiert** – *Länder (SVZ) · Kommunen (eigene Zählungen) ·
   Bund (BASt)* als je eine Gruppe mit Gruppen-Checkbox (an/aus/teilweise), Klapp-Pfeil
   und Anzahl. Kommunen zeigen das Bundesland-Kürzel („Ravensburg BW"). Die Titelzeile
   trennt ebenso: „SVZ: 11 Länder + BASt · dazu kommunale Zählungen: 2 Städte".
2. **⌖ hinzoomen** je Quelle (BBox aus dem Manifest) – für eine Stadt der einzige
   sinnvolle Weg, sie zu finden.
3. **Zoom-Hinweis im Gruppen-Kopf** („erst ab Zoom 8 · ⌖ zoomt hin") statt einer Zeile
   je Stadt – skaliert auf viele Einträge.
4. **Übersichts-Marker** auf Deutschland-Zoom: unterhalb Zoom 8 markiert je Stadt ein
   beschrifteter Punkt, *dass* es dort kommunale Daten gibt; Klick zoomt hin. Beim
   Hineinzoomen verschwinden die Marker, die echten Daten erscheinen.
5. **Ein Filter-Mechanismus für alles**: alle Pipeline-Layer filtern nach `source`;
   nur die extern gehostete UBA-HVS schaltet per Visibility.
6. **Popup** kennt die Ebene: Titel = Straßen-/Knotenname, Herausgeber „Ravensburg (BW)",
   Metrik-Badge **„24h-Zählung"** mit Tooltip („Einzelzählung … kein Jahresmittel"),
   Klasse „Gemeinde-/Stadtstraße".
7. **Zeichenreihenfolge**: Länder unten, Kommunen darüber (lokal detaillierter), BASt
   oben, Labels ganz oben.

### Optionen für später (wenn es > ~15 Kommunen werden)

- Kommunen-Gruppe **standardmäßig zugeklappt** ab N Einträgen; nur Marker + Gruppen-Kopf.
- **Nur Quellen im Kartenausschnitt** listen (BBox ∩ Viewport) – ein Toggle im Panel.
- **Suchfeld** über Namen (Städte + Länder).
- Kommunen **nach Bundesland** einrücken (die YAML kennt `state`).
- **Eigener Linienstil** für Einzelzählungen (`metric = 24h`), z.B. gestrichelt, damit
  die Färbung nicht suggeriert, es sei ein DTV.

## 5. Offene Punkte / Entscheidungen

- **Vergleichbarkeit der Metrik**: 24h-Einzelzählungen werden mit der DTV-Skala
  eingefärbt (sonst wären sie unsichtbar). Das Badge + Tooltip macht es kenntlich; ein
  eigener Stil (s. Option) wäre ehrlicher. Legendentitel nennt bislang nur DTV/DTVw.
- **Schwerverkehr Ravensburg**: SV-Anteil lt. Quelle Median ~18 % (bis 63 %) – deutlich
  über dem üblichen 5–10 %. Vermutlich inkl. Lieferwagen/Busse. Unverändert übernommen,
  im Adapter dokumentiert; ggf. beim Stadtplanungsamt nachfragen.
- **Rad/Fußgänger**: Ravensburg liefert sie mit. Option: optionale Spalten `dtv_rad`,
  `dtv_fuss` im Schema + dritter Legenden-Modus. Wäre ein echter Mehrwert kommunaler
  Daten gegenüber den Länder-SVZ.
- **Dedup Kommune ↔ Land**: Köln-Kanten liegen auf NRW-B/L/K-Linien. Koexistenz wie
  bei BASt (schaltbar). Ein sauberer Vorrang („Kommune vor Land im Stadtgebiet") wäre
  ein räumlicher Clip über die AGS-Grenze – offen.
- **Köln-Historie**: nur das ZIP 2016–2019 integriert; das ältere 2010–2016 nicht.
  Kölns Daten sind laut Stadt „für aktuelle Lärm-/Emissionsrechnungen nicht mehr
  geeignet" – im Panel steht 2019, im Popup das echte Jahr je Kante.
- **Bund-Ebene**: merge legt `level=bund` fest auf `svz_bast.fgb` (Punkte). Eine zweite
  Bund-Quelle mit Linien (z.B. Bundesfernstraßennetz-WFS) bräuchte die gleiche
  Linien/Punkte-Trennung wie Länder/Kommunen.
- **Deploy**: drittes PMTiles (`svz_kommunal.pmtiles`, ~1–2 MB) ist per `.gitignore`-
  Ausnahme im Repo, wie die anderen beiden.
- **`road_class` bei Kommunen**: `G` ist ein Sammelwert. Alternative wäre ein eigener
  Code „S" (Stadtstraße/unbekannt); bewusst nicht eingeführt, um die Enum klein zu halten.

## 6. Kandidaten-Sweep (Stand September 2026)

Systematische Suche über GovData-CKAN, Landesportale und Stadtportale (Methode und
Suchbegriffe: [AGENTS.md](../AGENTS.md)). Ergebnis:

| Stadt/Region | Land | Ergebnis |
|---|---|---|
| Düsseldorf | NW | ✅ integriert (GeoServer-WFS, DTVa 2024, SV über Geometrie-Join) |
| Lausitz (DiSTILL) | BB+SN | ⛔ verworfen: SVZ 2021 BB+SN auf OSM-Ways, alle 371 Zählstellen mit identischem DTV schon in bb/sn |
| Weingarten, Berg, Baienfurt, Baindt | BW | ✅ integriert (MobiData-BW-Format, generischer Adapter) |
| Frankfurt am Main | HE | 🔎 `research`: WFS vorhanden, GetFeature → 500; erste HE-Quelle, sobald der Dienst läuft |
| Münster | NW | ⛔ nur PDF/XLS je Einzelzählung (Spitzenstunden), Zählstellen-CSV ohne Werte |
| Potsdam | BB | ⛔ nur Knotenstandorte, Zählergebnisse als PDF-ZIP je Knoten |
| Dortmund | NW | ⛔ nur Zählstellenplan (Standorte 1998–2024), Werte kostenpflichtig auf Anfrage |
| Stuttgart | BW | ⛔ Kordon-Summen (Markungsgrenze/Kesselrand) ohne Koordinaten |
| Dresden | SN | 🔎 Themenstadtplan „Verkehrsmengen in Kfz/Tag" (Layer L1204–L1206); WFS-NodeId nicht gefunden, Portal 503 |
| Konstanz, Ettlingen, Gelsenkirchen | BW/NW | ⛔ Echtzeit-/Stundenwerte (DATEX, Sensoren), kein DTV |
| Mannheim, Leipzig, Heidelberg, Aachen | – | ⛔ nur Rad-Zählstellen |
| Kiel, Rostock, Bremen, Hannover, Bonn, Wuppertal, Bielefeld, München | – | keine maschinenlesbaren Kfz-Zählungen gefunden (oder Portal-API nicht erreichbar) |

Offen bleibt damit vor allem **Hessen** (Frankfurt) und eine Stadt in **Sachsen** (Dresden).
