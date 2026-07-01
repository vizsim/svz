# Verkehrsmengenkarte – SVZ der Bundesländer

Sammelt die **Straßenverkehrszählungs-/Verkehrsmengendaten (DTV)** der deutschen
Bundesländer aus ihren heterogenen Quellen (WFS / OGC API / ATOM-ZIP / GeoJSON /
Excel), bringt sie in **ein kanonisches Schema**, mergt sie und tilet sie zu **einer
`svz_de.pmtiles`**, die ein **MapLibre-Viewer** ([index.html](index.html)) auf
OpenFreeMap-Positron rendert. Pipeline + CLI: siehe [pipeline/README.md](pipeline/README.md).

**Stand: 11 Länder + BASt-Backbone (A+B) · 66.330 Segmente/Zählstellen** (Linien + Punkte;
Länder in `svz_de.pmtiles`, BASt separat schaltbar in `svz_bast.pmtiles`). Kanonische
Felder je Feature: `dtv_kfz`, `dtv_sv`, `sv_anteil`, `metric` (DTV/DTVw), `year`,
`road_class` (A/B/L/K/G), `road_no`, `station_id`, `state`, `source`, `license`.

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
mit den Länder-Daten (v.a. bei den Bundesstraßen) wegschaltbar bleibt. Details in [TODO.md](TODO.md).

## Datenquellen der 16 Bundesländer

Legende Status: ✅ live (implementiert) · 🔍 offen (Endpunkt gesucht) · ⛔ blockiert
(kein maschinenlesbarer DTV-Vektor). Zugang verlinkt den Endpunkt.

| Land | Status | Zugang (URL) | Geom | Jahr | Metrik | Lizenz | Features | Anmerkung |
|---|---|---|---|---|---|---|--:|---|
| **Baden-Württemberg** (BW) | ✅ | [GeoJSON](https://mobidata-bw.de/karten_geojsons/maps/count_car/SVZ-Zaehlstellen_231011_augmented_SVZ2024.geojson) | Punkte | 2024 | DTV | dl-de/by-2.0 | 5.629 | Zählstellen als **Punkte** (MobiData BW, `DTV2024`). |
| **Bayern** (BY) | ✅ | [WFS](https://gisportal-stmb.bayern.de/server/services/WFS/BAYSIS_Verkehrsdaten/MapServer/WFSServer) | Linien | 2021 | DTV | CC-BY-4.0 | 9.431 | BAYSIS (ArcGIS-WFS, GEOJSON); Staatsstr. „St" → L. |
| **Berlin** (BE) | ✅ | [WFS](https://gdi.berlin.de/services/wfs/verkehrsmengen_2023) | Linien | 2023 | **DTVw** | dl-de/zero-2.0 | 8.337 | Nur **Werktage** (DTVw); Kfz- + Lkw-Layer (Lkw → SV gejoint). |
| **Brandenburg** (BB) | ✅ | [WFS](https://inspire.brandenburg.de/services/zaehlstellen_wfs) | Linien | 2021 | DTV | dl-de/by-2.0 | 2.315 | Nativer `verkehrsstaerke_2021` (Geometrie **und** Werte in einem); nur GML, EPSG:25833. |
| **Bremen** (HB) | ⛔ | [Portal](https://bau.bremen.de/mobilitaet/verkehrsdaten/verkehrsmengenkarten-59016) | – | – | – | – | – | Nur **PDF**-Verkehrsmengenkarten (älter); A/B via BASt-Backbone. |
| **Hamburg** (HH) | ✅ | [WFS](https://geodienste.hamburg.de/HH_WFS_Verkehrsmengen) | Linien | 2019 | DTV | dl-de/by-2.0 | 4.303 | HVS- + BAB-Layer 2019 zusammengeführt; `sv` = SV-**Anteil %**. |
| **Hessen** (HE) | ⛔ | [Viewer](https://mobil.hessen.de/verkehr/interaktive-verkehrsmengenkarte) | – | – | – | – | – | Nur **interaktive Verkehrsmengenkarte / PDF**; Herausgabe maschinenlesbarer Daten verweigert. |
| **Mecklenburg-Vorpommern** (MV) | 🔍 | [Portal](https://www.geoportal-mv.de/) | – | 2021 | DTV | dl-de/by-2.0 | – | WFS-/SVZ-Endpunkt noch nicht verifiziert; als Info eine **[Verkehrsmengenkarte 2021 (PDF)](https://www.strassen-mv.de/static/LSBV/Dateien/Downloads/Verkehrsmengenkarten/vmk2021.pdf)** (LSBV M-V). |
| **Niedersachsen** (NI) | ✅ | [ZIP](https://map.strassenbau.niedersachsen.de/zip/DE-NI-SBV_Downloadservice_SVZ_Zaehlstellenbereiche_2021.zip) | Linien | 2021 | DTV | dl-de/by-2.0 | 2.819 | INSPIRE-Downloadservice-**ZIP** (Shapefile), EPSG:25832. |
| **Nordrhein-Westfalen** (NW) | ✅ | [ZIP](https://www.opengeodata.nrw.de/produkte/transport_verkehr/strassennetz/Verkehrswerte2019HR_EPSG25832_Shape.zip) | Linien | 2019 | DTV | dl-de/by-2.0 | 13.858 | opengeodata-**Shapefile** (`DTVKFZA`); nur B/L/K (**keine Autobahnen**). |
| **Rheinland-Pfalz** (RP) | ⛔ | [OGC API](https://www.geoportal.rlp.de/spatial-objects/393) | – | 2021 | DTV | dl-de/by-2.0 | – | OGC API Features (`DTV_WFS:SVZ{Jahr}_Zaehlstellenbereiche`) vorhanden, Server liefert aber konstant **DB-Fehler** → warten. Als Info das **[Verkehrsstärkenkarten-Portal (LBM)](https://lbm.rlp.de/themen/strassendaten/verkehrsstaerkenkarten)**. |
| **Saarland** (SL) | ✅ | [WFS](https://geoportal.saarland.de/arcgis/services/Internet/Verkehr_WFS/MapServer/WFSServer) | Punkte | 2021 | DTV | offen | 757 | Zählstellen als **Punkte** (ArcGIS); brauchte `srs=CRS:84` (EPSG:4326 tauschte lat/lon). |
| **Sachsen** (SN) | ✅ | [ZIP](https://www.list.smwa.sachsen.de/gdi/download/DE-SN-SBV-SVZ2021.zip) | Linien | 2021 | DTV | dl-de/by-2.0 | 3.510 | GDI-SBV-**Shapefile-ZIP**; Staatsstr. „S" → L. |
| **Sachsen-Anhalt** (ST) | ✅ | [WFS](https://www.geodatenportal.sachsen-anhalt.de/gfds/ws/wfs/a78d7bc1-ffbb-cf76/GDI-LSA_LSBB_STRASSENNETZE/ows.wfs) + [Excel](https://lsbb.sachsen-anhalt.de/fileadmin/Bibliothek/Politik_und_Verwaltung/Landesbetriebe/LSBB/Service/Strassenverkehrszaehlungen/Dateien_2025/Ergebnisse_SVZ_2021.xlsx) | Linien | 2021 | DTV | dl-de/by-2.0 | 1.145 | **Netz-WFS × DTV-Excel** über Netzknoten `(VonNK,NachNK)` gejoint (WFS = nur Geometrie). |
| **Schleswig-Holstein** (SH) | ⛔ | [WFS](https://service.gdi-sh.de/WFS_SH_Strasseninfo) | – | 2021 | DTV | CC-BY-4.0 | – | WFS **nur Netzgeometrie**. Fürs L/K-Netz **keine maschinenlesbare DTV** (LBV.SH lt. [FragDenStaat](https://fragdenstaat.de/anfrage/zaehlstellen-zaehlstellenkarte-verkehrsmengenkarte/)); nur eine **[Verkehrsmengenkarte 2015 als PDF](https://schleswig-holstein.de/mm/downloads/LBVSH/Aufgaben/Strassenbau/verkehrsmengenkarte2015.pdf)**; A/B nur über BASt. |
| **Thüringen** (TH) | ✅ | [WFS](https://www.geoproxy.geoportal-th.de/geoproxy/services/STRNETZ_SVZ_wfs) | Linien | 2015 | DTV | dl-de/by-2.0 | 2.276 | **WFS 1.1.0** (nicht 2.0!); Zählstellenbereiche-Linien × Verkehrsmengen-Werte über `(zst_nr,von_stat,bis_stat)` gejoint. |
| **Bund – BASt** (A+B) | ✅ | [Excel A](https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/2021/Autobahnen-2021.xlsx?__blob=publicationFile&v=1) · [Excel B](https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/2021/Bundesstrassen-2021.xlsx?__blob=publicationFile&v=1) | Punkte | 2021 | DTV | CC-BY-4.0 | 11.950 | **Bundesweiter Backbone** (Bundesfernstraßen A+B, X/Y-Koordinaten UTM32N) → füllt die A-Lücke (NW/BE); `state=DE`, `source=bast`. Eigenes **`svz_bast.pmtiles`, im Frontend separat schaltbar**. |

Blockierte/offene Länder sind in [TODO.md](TODO.md) detailliert. Ein wiederkehrendes
Muster: einige Länder liefern nur **Netzgeometrie ohne DTV** (SH, ST-WFS) oder DTV nur
als **PDF** (HB, HE, SH-L/K) – dann braucht es eine Werte-Tabelle mit Netzknoten/
Zählstellennummer zum Join (wie ST/TH). Autobahnen decken bundesweit der **BASt-Backbone**
ab (die Länder liefern A seit der Autobahn GmbH teils nicht mehr).

## Aufbau

```text
svz/
├─ index.html · main.js · style.css   # MapLibre-Viewer (OpenFreeMap Positron)
├─ pipeline/                           # uv-Paket "svzkarte": Adapter -> merge -> tiles
│  ├─ src/svzkarte/adapters/<code>.py  # ein Adapter je Land, normalize() -> GeoDataFrame
│  ├─ config/sources.yaml              # je Land: status/kind/url/year/license/metric
│  └─ config/tiles.yaml                # tippecanoe-Profile (svz_lines / svz_points)
├─ TODO.md                             # Datenlücken, BASt-Backbone, offene Punkte
└─ docs/                               # Screenshots
```
