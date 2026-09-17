![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue)

# Verkehrsmengenkarte – SVZ der Bundesländer (+ kommunale Zählungen)

Sammelt die **Straßenverkehrszählungs-/Verkehrsmengendaten (DTV)** der deutschen
Bundesländer aus ihren heterogenen Quellen (WFS / OGC API / ATOM-ZIP / GeoJSON / CSV /
Excel), bringt sie in **ein kanonisches Schema**, mergt sie und tilet sie zu **einer
`svz_de.pmtiles`**, die ein **MapLibre-Viewer** ([index.html](index.html)) auf
OpenFreeMap-Positron rendert; den Autobahn-/Bundesstraßen-Backbone liefert die BASt.
**Ergänzend – und begrifflich getrennt –** nimmt die Karte **kommunale Verkehrszählungen**
einzelner Städte auf: das sind **keine SVZ-Daten**, sondern eigene Erhebungen der
Kommunen (s. [Kommunale Verkehrszählungen](#kommunale-verkehrszählungen-keine-svz)).
Pipeline + CLI: siehe [pipeline/README.md](pipeline/README.md).

**Stand: SVZ 11 Länder + BASt-Backbone (A+B) · 66.339 Segmente/Zählstellen** (Linien +
Punkte; Länder in `svz_de.pmtiles`, BASt separat schaltbar in `svz_bast.pmtiles`) **·
dazu kommunale Zählungen aus 8 Kommunen (Köln, Düsseldorf, Frankfurt am Main, Ravensburg,
Weingarten, Berg, Baienfurt, Baindt) · 5.276 Kanten/Zählstellen** in `svz_kommunal.pmtiles`.
Kanonische Felder je Feature: `dtv_kfz`, `dtv_sv`, `sv_anteil`, `metric` (DTV/DTVw/24h),
`year`, `road_class` (A/B/L/K/G), `road_no`, `name`, `station_id`, `state`, `source`,
`level` (bund/land/kommune), `license`. Wie man Quellen findet und verarbeitet:
[AGENTS.md](AGENTS.md).

## Hintergrund: SVZ, Zuständigkeiten, BASt

Die **Straßenverkehrszählung (SVZ)** wird bundesweit **alle ~5 Jahre** nach mehr oder
weniger einheitlicher Methodik erhoben (die reguläre Zählung 2020 wurde coronabedingt
auf **2021** verschoben; SVZ 2025 ist in Aufbereitung). Erhoben wird also gemeinsam –
**verwaltet und bereitgestellt** werden die Daten aber **je Bundesland von
unterschiedlichen Institutionen** (Landesbetriebe für Straßenbau, Ministerien,
Vermessungs-/GDI-Stellen) und entsprechend **in ganz unterschiedlichen Formaten und
unter wechselnden Bezeichnungen**. Genau das macht dieses Projekt nötig – und die
Quellensuche mühsam. Nützliche **Suchbegriffe**:
*SVZ* · *Straßenverkehrszählung* · *Verkehrsmengen* · *Verkehrsmengenkarte* ·
*Verkehrsstärke* · *Zählstellen* · *Zählstellenbereiche*.

Bundesweit bündelt die **BASt** (Bundesanstalt für Straßenwesen) die SVZ der
**Bundesfernstraßen (Autobahnen + Bundesstraßen)** und stellt Einzelergebnisse (Excel
mit Koordinaten) sowie das Bundesfernstraßennetz bereit – das deckt allerdings **nur
A/B** ab, nicht das nachgeordnete Landes-/Kreisnetz, und liegt wieder in eigenem
Format vor.

Seit Gründung der **Autobahn GmbH des Bundes (2021)** sind die Länder **nicht mehr für
die Autobahnen zuständig** – einige veröffentlichen die **Autobahn-Daten deshalb nicht
mehr** (z.B. NRW gar keine, Berlin nur Reste). Diese Lücke schließt der
**BASt-Backbone**: die bundesweite BASt-SVZ 2021 der **Bundesfernstraßen (A + B)** ist
als Punkte (mit DTV, aus den X/Y-Koordinaten der Zählstellen) integriert – in einem
**eigenen, im Frontend ein-/ausblendbaren** `svz_bast.pmtiles`, sodass die Überlappung
mit den Länder-Daten (v.a. bei den Bundesstraßen) wegschaltbar bleibt. Details in [TODO.md](docs/TODO.md).

## Datenquellen der 16 Bundesländer

Legende Status: ✅ live (implementiert) · ⛔ blockiert
(kein maschinenlesbarer DTV-Vektor). Zugang verlinkt den Endpunkt. Spalte **SV**
(Schwerverkehr): `abs` = absolute Menge (`dtv_sv`) · `%` = Anteil (`sv_anteil`) · `–` keiner.

| Land | Status | Zugang (URL) | Geom | Jahr | Metrik | SV | Lizenz | Features | Anmerkung |
|---|---|---|---|---|---|---|---|--:|---|
| **Baden-Württemberg** (BW) | ✅ | [CSV](https://mobidata-bw.de/vm/Karte_Strassenverkehrszaehlung_BW/SVZ-Zaehlstellen_2026-06-26_augmented_SVZ2024.csv) · [Portal](https://mobidata-bw.de/dataset/karte_strassenverkehrszaehlung) | Punkte | 2024 | DTV | abs | dl-de/by-2.0 | 5.638 | Zählstellen als **Punkte** (MobiData BW, `DTV2024`, Koordinaten `gpsx1`/`gpsy1`). Bis 09/2026 als GeoJSON veröffentlicht (jetzt 404); die CSV mit Stand 2026-06-26 trägt dieselben Werte. Standdatum steckt im Dateinamen → bei 404 im Portal-Datensatz nach der neuen Ressource schauen. |
| **Bayern** (BY) | ✅ | [WFS](https://gisportal-stmb.bayern.de/server/services/WFS/BAYSIS_Verkehrsdaten/MapServer/WFSServer) | Linien | 2021 | DTV | abs | CC-BY-4.0 | 9.431 | BAYSIS (ArcGIS-WFS, GEOJSON); Staatsstr. „St" → L. |
| **Berlin** (BE) | ✅ | [WFS](https://gdi.berlin.de/services/wfs/verkehrsmengen_2023) | Linien | 2023 | **DTVw** | abs | dl-de/zero-2.0 | 8.337 | Nur **Werktage** (DTVw); Kfz- + Lkw-Layer (Lkw → SV gejoint). |
| **Brandenburg** (BB) | ✅ | [WFS](https://inspire.brandenburg.de/services/zaehlstellen_wfs) | Linien | 2021 | DTV | abs · % | dl-de/by-2.0 | 2.315 | Nativer `verkehrsstaerke_2021` (Geometrie **und** Werte in einem); nur GML, EPSG:25833. |
| **Bremen** (HB) | ⛔ | [Portal](https://bau.bremen.de/mobilitaet/verkehrsdaten/verkehrsmengenkarten-59016) | – | – | – | – | – | – | Nur **PDF**-Verkehrsmengenkarten (älter); A/B via BASt-Backbone. |
| **Hamburg** (HH) | ✅ | [WFS](https://geodienste.hamburg.de/HH_WFS_Verkehrsmengen) | Linien | 2019 | DTV | % | dl-de/by-2.0 | 4.303 | HVS- + BAB-Layer 2019 zusammengeführt; `sv` = SV-**Anteil %**. |
| **Hessen** (HE) | ⛔ | [Viewer](https://mobil.hessen.de/verkehr/interaktive-verkehrsmengenkarte) | – | – | – | – | – | – | Nur **interaktive Verkehrsmengenkarte / PDF**; Herausgabe maschinenlesbarer Daten verweigert. Bisher einzige HE-Daten: kommunale Zählungen [Frankfurt](#kommunale-verkehrszählungen-keine-svz). |
| **Mecklenburg-Vorpommern** (MV) | ⛔ | [VMK 2021 (PDF)](https://www.strassen-mv.de/static/LSBV/Dateien/Downloads/Verkehrsmengenkarten/vmk2021.pdf) | – | 2021 | DTV | – | dl-de/by-2.0 | – | Nur **PDF** (Verkehrsmengenkarte 2021, LSBV M-V); ein maschinenlesbarer WFS (Übersicht: SVZ 2015) ließ sich nicht verifizieren. |
| **Niedersachsen** (NI) | ✅ | [ZIP](https://map.strassenbau.niedersachsen.de/zip/DE-NI-SBV_Downloadservice_SVZ_Zaehlstellenbereiche_2021.zip) | Linien | 2021 | DTV | abs | CC-BY-4.0 | 2.819 | INSPIRE-Downloadservice-**ZIP** (Shapefile), EPSG:25832. Lizenz lt. INSPIRE-Record (CC BY 4.0). |
| **Nordrhein-Westfalen** (NW) | ✅ | [ZIP](https://www.opengeodata.nrw.de/produkte/transport_verkehr/strassennetz/Verkehrswerte2019HR_EPSG25832_Shape.zip) | Linien | 2019 | DTV | abs | dl-de/by-2.0 | 13.858 | opengeodata-**Shapefile** (`DTVKFZA`); nur B/L/K (**keine Autobahnen**). |
| **Rheinland-Pfalz** (RP) | ⛔ | [OGC API](https://www.geoportal.rlp.de/spatial-objects/393) | – | 2021 | DTV | – | dl-de/by-2.0 | – | OGC API Features (`DTV_WFS:SVZ{Jahr}_Zaehlstellenbereiche`) vorhanden, Server liefert aber konstant **DB-Fehler** → warten. Als Info das **[Verkehrsstärkenkarten-Portal (LBM)](https://lbm.rlp.de/themen/strassendaten/verkehrsstaerkenkarten)**. |
| **Saarland** (SL) | ✅ | [WFS](https://geoportal.saarland.de/arcgis/services/Internet/Verkehr_WFS/MapServer/WFSServer) | Punkte | 2021 | DTV | abs | CC-BY-4.0 | 757 | Zählstellen als **Punkte** (ArcGIS); brauchte `srs=CRS:84` (EPSG:4326 tauschte lat/lon). |
| **Sachsen** (SN) | ✅ | [ZIP](https://www.list.smwa.sachsen.de/gdi/download/DE-SN-SBV-SVZ2021.zip) | Linien | 2021 | DTV | abs · % | dl-de/by-2.0 | 3.510 | GDI-SBV-**Shapefile-ZIP**; Staatsstr. „S" → L. |
| **Sachsen-Anhalt** (ST) | ✅ | [WFS](https://www.geodatenportal.sachsen-anhalt.de/gfds/ws/wfs/a78d7bc1-ffbb-cf76/GDI-LSA_LSBB_STRASSENNETZE/ows.wfs) + [Excel](https://lsbb.sachsen-anhalt.de/fileadmin/Bibliothek/Politik_und_Verwaltung/Landesbetriebe/LSBB/Service/Strassenverkehrszaehlungen/Dateien_2025/Ergebnisse_SVZ_2021.xlsx) | Linien | 2021 | DTV | abs | dl-de/by-2.0 | 1.145 | **Netz-WFS × DTV-Excel** über Netzknoten `(VonNK,NachNK)` gejoint (WFS = nur Geometrie). |
| **Schleswig-Holstein** (SH) | ⛔ | [WFS](https://service.gdi-sh.de/WFS_SH_Strasseninfo) | – | 2021 | DTV | – | CC-BY-4.0 | – | WFS **nur Netzgeometrie**. Fürs L/K-Netz **keine maschinenlesbare DTV** (LBV.SH lt. [FragDenStaat](https://fragdenstaat.de/anfrage/zaehlstellen-zaehlstellenkarte-verkehrsmengenkarte/)); nur eine **[Verkehrsmengenkarte 2015 als PDF](https://schleswig-holstein.de/mm/downloads/LBVSH/Aufgaben/Strassenbau/verkehrsmengenkarte2015.pdf)**; A/B nur über BASt. |
| **Thüringen** (TH) | ✅ | [WFS](https://www.geoproxy.geoportal-th.de/geoproxy/services/STRNETZ_SVZ_wfs) | Linien | 2015 | DTV | abs | dl-de/by-2.0 | 2.276 | **WFS 1.1.0** (nicht 2.0!); Zählstellenbereiche-Linien × Verkehrsmengen-Werte über `(zst_nr,von_stat,bis_stat)` gejoint. |
| **Bund – BASt** (A+B) | ✅ | [Excel A](https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/2021/Autobahnen-2021.xlsx?__blob=publicationFile&v=1) · [Excel B](https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/2021/Bundesstrassen-2021.xlsx?__blob=publicationFile&v=1) | Punkte | 2021 | DTV | abs | © BASt | 11.950 | **Bundesweiter Backbone** (Bundesfernstraßen A+B, X/Y-Koordinaten UTM32N) → füllt die A-Lücke (NW/BE); `state=DE`, `source=bast`. Eigenes **`svz_bast.pmtiles`, im Frontend separat schaltbar**. |
| **Bund – UBA HVS** | ✅ | [UBA-Lärmkartierung (Viewer)](https://gis.uba.de/maps/resources/apps/laermkartierung/index.html?lang=de) | Linien | 2021 | DTV≈ | – | © UBA | bundesweit | **Hauptverkehrsstraßen (UBA/END 4. Runde)**, Attribut `annualTrafficFlow` (Kfz/Jahr) → als **DTV≈** (÷365) eingefärbt. Gehostete PMTiles aus [unfallkarte](https://tiles.vizsim.de/file/unfallkarte-data-v2/uba/hvs_verkehrsmengen.pmtiles); im Frontend **initial ausgeblendeter Fallback/Backbone** (nur ab Zoom 9). |

Blockierte/offene Länder sind in [TODO.md](docs/TODO.md) detailliert. Ein wiederkehrendes
Muster: einige Länder liefern nur **Netzgeometrie ohne DTV** (SH, ST-WFS) oder DTV nur
als **PDF** (HB, HE, SH-L/K) – dann braucht es eine Werte-Tabelle mit Netzknoten/
Zählstellennummer zum Join (wie ST/TH). Autobahnen decken bundesweit der **BASt-Backbone**
ab (die Länder liefern A seit der Autobahn GmbH teils nicht mehr).

## Kommunale Verkehrszählungen (keine SVZ)

Ergänzend zur SVZ nimmt die Karte **eigene Zählungen einzelner Städte** auf – das sind
**keine SVZ-Daten**: die Kommunen erheben selbst, mit eigener Methodik und ohne den
bundesweiten Turnus. Sie werden deshalb als **eigene Ebene** geführt und im Viewer
begrifflich abgesetzt („Kommunen – eigene Zählungen"; Konzept:
[docs/Konzept_kommunale_daten.md](docs/Konzept_kommunale_daten.md),
[Issue #1](https://github.com/vizsim/svz/issues/1)). Methodische Unterschiede: oft
**24h-Einzelzählungen an einem Werktag** statt Jahresmittel (Metrik **`24h`**, im Popup
„24h-Zählung"), **Zähljahr je Zählstelle**, keine Straßenklasse (→ `G` =
Gemeinde-/Stadtstraße), dafür Straßen-/Knotenname (`name`). Sie liegen in einem eigenen
`svz_kommunal.pmtiles` (Layer `kommunal` + `kommunal_points`, **erst ab Zoom 8**); auf
Deutschland-Zoom markiert ein beschrifteter Punkt je Stadt, dass es dort Daten gibt
(Klick zoomt hin). Adapter unter
[pipeline/src/svzkarte/adapters/kommunal/](pipeline/src/svzkarte/adapters/kommunal/).

| Stadt | Land | Status | Zugang (URL) | Geom | Jahr | Metrik | SV | Lizenz | Features | Anmerkung |
|---|---|---|---|---|---|---|---|---|--:|---|
| **Düsseldorf** | NW | ✅ | [WFS](https://maps.duesseldorf.de/services/verkehrszaehlung/wfs?service=WFS&request=GetCapabilities) · [Portal](https://opendata.duesseldorf.de/dataset/verkehrsz%C3%A4hldaten-d%C3%BCsseldorf-2024) | Linien | 2024 | DTV | abs | dl-de/zero-2.0 | 2.089 | GeoServer-WFS mit einem Layer je Fahrzeugart; **DTVa** = Mittel der Zählungen 2020–2024 (sonst 2015–2024), hochgerechnet aus 16h-Werktagszählungen. SV = Lkw oA + Lkw mA + Bus, über identische Geometrien gejoint. |
| **Frankfurt am Main** | HE | ✅ | [WFS](https://geowebdienste.frankfurt.de/Verkehrsmengen?service=WFS&request=GetCapabilities) · [Portal](https://opendata.hessen.de/dataset/wfs-verkehrsmengen-frankfurt-am-main) | Linien | 2019–2023 | **24h** | abs | dl-de/by-2.0 | 530 | GeoServer-WFS des Straßenverkehrsamts, ein Layer je Fahrzeugart, Join über die Abschnittsnummer `str_nr`. Werte = **Mittel der Werktagszählungen 2019–2023** (Zähltage nur Di–Do, keine Hochrechnung aufs Jahr → `24h`, nicht DTV). SV = Lkw mit + ohne Anhänger (kein Bus-Layer; nur für 409 Abschnitte). Rad-Layer vorhanden, noch ungenutzt. **Erste Quelle in Hessen** (bis 09/2026 lieferte der Dienst nur HTTP 500). |
| **Köln** | NW | ✅ | [ZIP](https://www.offenedaten-koeln.de/sites/default/files/distribution/KFZ%2520Zaehldaten%25202016-2019_0.zip) · [Portal](https://www.offenedaten-koeln.de/dataset/kfz-zaehlstellen-und-werte-koeln) | Linien | 2016–2019 | **DTVw** | – | dl-de/zero-2.0 | 2.551 | VISUM-Netzexport (Shapefile, GK2), Werte **je Richtung und Jahr**; je Kante jüngstes Jahr mit beiden Richtungen (Summe), sonst eine Richtung. Nur Kanten mit Werten. |
| **Ravensburg** | BW | ✅ | [Excel](https://mobidata-bw.de/daten/portal/RV_Zaehl/Verkehrszaehlungen_RV.xlsx) · [Portal](https://mobidata-bw.de/dataset/zaehldaten-ravensburg) | Punkte | 2023–2026 | **24h** | abs | dl-de/by-2.0 | 96 | Knotenpunkt-Zählungen (Di/Do, 24 h), je Zählstelle die **jüngste** Zählung; SV lt. Quelle auffällig hoch (Median ~18 %). Rad/Fuß im Excel enthalten, noch nicht im Schema. |
| **Weingarten** | BW | ✅ | [Excel](https://mobidata-bw.de/daten/portal/WGT_Zaehl/Verkehrszaehlungen-Stadt-Weingarten.xlsx) · [Portal](https://mobidata-bw.de/dataset/zaehldaten-stadt-weingarten) | Punkte | 2023–2026 | **24h** | abs | dl-de/by-2.0 | 7 | Gleiches MobiData-BW-Format wie Ravensburg → **ein generischer Adapter** (`kommunal/mobidata_bw.py`), nur ein YAML-Eintrag je Kommune. |
| **Berg** · **Baienfurt** · **Baindt** | BW | ✅ | [Berg](https://mobidata-bw.de/dataset/zaehldaten-gemeinde-berg) · [Baienfurt](https://mobidata-bw.de/dataset/zaehldaten-gemeinde-baienfurt) · [Baindt](https://mobidata-bw.de/dataset/zaehldaten-gemeinde-baindt) | Punkte | 2026 | **24h** | abs | dl-de/by-2.0 | je 1 | Schussental-Gemeinden, je eine Zählstelle, derselbe Adapter. Zeigen, dass kleine Kommunen ohne Code-Änderung dazukommen. |

Geprüft und (vorerst) verworfen: Münster (nur PDF/XLS je Einzelzählung), Potsdam (nur
Knotenstandorte + PDF), Dortmund (Zählstellenplan, Werte kostenpflichtig), Stuttgart
(Kordon-Summen ohne Koordinaten), Dresden (Themenstadtplan-Thema vorhanden, WFS-Knoten
nicht auffindbar), Konstanz/Mannheim/Leipzig/Heidelberg (nur Rad bzw. Echtzeit),
**Lausitz (DiSTILL, Mobilithek)**: legt die SVZ 2021 von BB+SN auf OSM-Ways – alle 371
Zählstellen sind mit identischem DTV schon in den Landesdaten, also kein Mehrwert. Details
und Suchstrategie in [AGENTS.md](AGENTS.md). Neue Stadt = Eintrag in `sources.yaml` +
Adapter-Datei (oder `adapter:` auf einen generischen) + Golden-Test; das Frontend-Panel
baut sich aus `data/manifest.json`.

**Fehlt eine Zählung?** Du kennst eine offizielle Quelle (Bundesland oder Stadt/Gemeinde),
die hier noch nicht drin ist? **[Kurz melden](https://github.com/vizsim/svz/issues/new?template=fehlende-zaehlung.yml)** –
Ort und Link genügen, den Rest übernehmen wir.

## Aufbau

```text
svz/
├─ AGENTS.md                           # Learnings: Quellen finden, Quellentypen, Verarbeitungsmuster, Sackgassen
├─ index.html · main.js · style.css   # MapLibre-Viewer (OpenFreeMap Positron); Quellen-Panel aus manifest.json
├─ pipeline/                           # uv-Paket "svzkarte": Adapter -> merge (je Ebene) -> tiles
│  ├─ src/svzkarte/adapters/<code>.py  # ein Adapter je Land/Bund (SVZ), normalize() -> GeoDataFrame
│  ├─ src/svzkarte/adapters/kommunal/  # Kommunen: koeln.py, duesseldorf.py, mobidata_bw.py (generisch, normalize(code))
│  ├─ config/sources.yaml              # DIE Quellenliste: level/name/state/status/kind/url/year/license/access
│  ├─ config/tiles.yaml                # tippecanoe-Profile (svz_lines/svz_points/bast_points/kommunal_*)
│  └─ data/manifest.json               # generiert (`svz manifest`): Datensätze + Quellen (bbox) fürs Frontend
├─ docs/
│  ├─ Konzept_kommunale_daten.md       # Konzept dritte Ebene „Kommunen" (Issue #1)
│  ├─ TODO.md                          # Datenlücken, BASt-Backbone, offene Punkte
│  └─ cdp_shot.py                      # Headless-Screenshot-Tooling (CDP)
└─ .github/ISSUE_TEMPLATE/             # Issue-Formular: fehlende Zählung melden (Ort + Link)
```

## Lizenz

**Code: [AGPL-3.0-or-later](LICENSE)** © vizsim. Der Quellcode-Link im UI (Panel-Footer)
erfüllt die AGPL-§13-Pflicht (Network Use).

**Daten** behalten ihre **jeweilige Quell-Lizenz** (Spalte „Lizenz" in den Tabellen oben:
dl-de/by-2.0 · CC-BY-4.0 · dl-de/zero-2.0 · © BASt · © UBA) und **erfordern
Namensnennung** – `svz_de.pmtiles`/`svz_bast.pmtiles`/`svz_kommunal.pmtiles` sind nur
eine umgepackte Ableitung, keine eigene Lizenzierung der Inhalte. Attribution des
Herausgebers trägt jedes Feature im Feld `license`/`source`/`level`.

**Basiskarte:** [OpenFreeMap](https://openfreemap.org/) · OpenMapTiles ·
[OpenStreetMap](https://www.openstreetmap.org/copyright)-Daten (ODbL).
