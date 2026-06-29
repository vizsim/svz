# SVZ / Verkehrsmengen der Bundesländer – Quellenübersicht

Stand der Recherche: Juni 2026. Bezug: Issue [vizsim/unfallkarte#12](https://github.com/vizsim/unfallkarte/issues/12).

**Zeitlicher Rahmen (für alle Länder gleich):** Die bundesweite Straßenverkehrszählung (SVZ) läuft im 5-Jahres-Turnus. Die für 2020 geplante Zählung wurde wegen Corona auf **2021** verschoben → **SVZ 2021 ist überall der aktuellste vollständige Stand**. Die **SVZ 2025** wurde 2024–2025 erhoben; Ergebnisse voraussichtlich **ab Ende 2026**. Einige Dienste zeigen noch ältere Stände.

**Zentrale Kenngröße:** DTV (durchschnittliche tägliche Verkehrsstärke, alle Tage Mo–So). Achtung Vergleichbarkeit: Berlin/Hamburg liefern z.T. **DTVw** (nur Werktage) – nicht direkt mit DTV mischbar.

---

## Übersicht aller 16 Länder

| Land | Stelle & Portal | Zugang / Format | Aktuellstes Jahr | Nachgeordnetes Netz (L/K) | Lizenz |
|---|---|---|---|---|---|
| **Baden-Württemberg** | Verkehrsministerium BW – [MobiData BW (Endergebnisse)](https://mobidata-bw.de/dataset/endergebnisse_strassenverkehrszaehlung) + [Zählstellen-Karte](https://mobidata-bw.de/dataset/karte_strassenverkehrszaehlung) | **Excel (XLSX, gezippt) + PDF**, jahresweise; CKAN-API. Werte tabellarisch je Zählstelle → Join mit Zählstellen-Geometrie | **jährlich 2010–2024** (Monitoring) | A/B/L/**K** (alle Klassen) | dl-de/by-2.0 |
| **Bayern** | Bayerische Straßenbauverwaltung – [BAYSIS](https://www.baysis.bayern.de/internet/verdat/svz/) | **WFS + WMS** | SVZ 2021 (+ Monitoring seit 2016, jährl.) | Staatsstr. + Großteil Kreisstr. | CC-BY 4.0 |
| **Berlin** | SenMVKU – [Berlin Open Data / gdi.berlin.de](https://daten.berlin.de/datensaetze/verkehrsmengen-dtvw-2019-wfs-44f64418) | **WFS** | **DTVw 2019** | übergeordnetes Hauptstraßennetz | dl-de/zero-2.0 |
| **Brandenburg** | Landesbetrieb Straßenwesen (LS) – [Geoportal Brandenburg](https://www.ls.brandenburg.de/ls/de/service/karten/verkehrsstaerkenkarte/) | **WFS + WMS** (Zählstellenbereiche + Verkehrsstärkedaten) + Viewer | SVZ 2021 (2025 erst Standorte) | A/B/L (K nur nachrichtlich) | dl-de/by-2.0 (HVD) |
| **Bremen** | Senatorin f. Bau, Mobilität – [bau.bremen.de](https://bau.bremen.de/mobilitaet/verkehrsdaten/verkehrsmengenkarten-59016) / GeoPortal Bremen | nur **PDF** (Verkehrsmengenkarten); kein DTV-Dienst gefunden | älter (gefunden 2005/2010); A/B via BASt | begrenzt, Hauptstraßen | CC-BY 4.0 |
| **Hamburg** | BVM – [Transparenzportal Hamburg](https://suche.transparenz.hamburg.de/dataset/verkehrsmengen-auf-hauptverkehrsstrassen-in-hamburg43) | **WFS + WMS + GML** | Verkehrsmengenkarte 2019; DTV/DTVw jährl. | Hauptverkehrsstraßen (aus Verkehrsmodell) | dl-de/by-2.0 |
| **Hessen** | Hessen Mobil – [Interaktive Verkehrsmengenkarte](https://mobil.hessen.de/verkehr/interaktive-verkehrsmengenkarte) | nur **Viewer + PDF** (Shape-Herausgabe verweigert) | SVZ 2021 (2025 → Nov 2026) | B/L/K (~3.400 Zählst.) | eingeschränkt / Urheberrecht |
| **Mecklenburg-Vorp.** | LSBV M-V – [GeoPortal MV](https://www.geoportal-mv.de/portal/Suche/Metadatenuebersicht/Details/Verkehrsmengen%20M-V/1f815cae-3332-4442-8c64-f197ef3638e6) | **WMS + WFS** (DTV + SV) | SVZ **2015** im Dienst (2021 ggf. nachgezogen) | A/B/L | dl-de/by-2.0 (prüfen) |
| **Niedersachsen** | NLStBV – [Geofachdaten INSPIRE](https://www.strassenbau.niedersachsen.de/startseite/service/geofachdaten_und_wms_kartendienste/geofachdaten-und-wms-kartendienste-133771.html) + [OpenGeoData.NI](https://ni-lgln-opengeodata.hub.arcgis.com/) | **WMS + INSPIRE-Downloaddienst (WFS/ATOM)**, Zählstellenbereiche mit DTV + DTVSV; ArcGIS-Hub-Download (GeoJSON/CSV) | SVZ 2021 (+ 2015/2010) | A/B/L (~2.700; keine K) | dl-de/by-2.0 |
| **Nordrhein-Westf.** | Straßen.NRW – [periodische Verkehrszählungen](https://www.strassen.nrw.de/de/periodische-verkehrszaehlungen.html) + [Geoportal NRW Open Data](https://www.wms.nrw.de/rssfeeds/content/geoportal/html/1004.html) | **Shape-File** (Atom-Feed) + WMS | SVZ 2021 (+ Netz 2019) | A/B/L/K (~7.710 Zählst., inkl. Lärmkennwerte) | dl-de/by-2.0 |
| **Rheinland-Pfalz** | LBM – [GeoPortal RLP (OGC API/WFS)](https://www.geoportal.rlp.de/spatial-objects/393) + [Mobilitätsatlas](https://lbm.rlp.de/themen/strassendaten/verkehrsstaerkenkarten) | **OGC API Features / WFS** (`DTV_WFS:SVZ…_Zaehlstellenbereiche`) + Viewer | SVZ (mind. 2010er-Collection; neuere prüfen) | B/L/K | dl-de/by-2.0 |
| **Saarland** | LfS – [geoportal.saarland.de](https://geoportal.saarland.de) + [saarland.de PDF](https://www.saarland.de/lfs/DE/service/verkehrsmengenkarte/verkehrsmengenkarte) | **WMS** (DTV + DTVSV) + PDF | SVZ 2021 (L II.O 2015) | bis Landstr. 2. Ordnung | offen (INSPIRE, keine Beschränkung) |
| **Sachsen** | LASuV / LISt (GDI-SBV) – [GovData](https://www.govdata.de/suche/daten/strassenverkehrszahlungen-svz-in-sachsen99855) | **WFS + WMS** | SVZ 2021 (+ 2019 Hochr.) | A/B/Staats-/Kreisstr. | dl-de/by-2.0 |
| **Sachsen-Anhalt** | LSBB – [lsbb.sachsen-anhalt.de](https://lsbb.sachsen-anhalt.de/service/manuelle-strassenverkehrszaehlungen) + [Geodatenportal ST](https://www.geodatenportal.sachsen-anhalt.de) | **PDF/Excel** (Ergebnisse) + WFS/WMS (Straßennetz) | SVZ 2021 | B/L (Netz-WFS inkl. K) | dl-de/by-2.0 |
| **Schleswig-Holstein** | LBV.SH – [GDI-SH / geoportal.de](https://www.geoportal.de/Metadata/4db88cf7-23d6-4207-a3da-8ab1a94508ba) | **WFS** (Straßeninformationen / Verkehrsnetze) | SVZ 2021 (2025 lief bis Okt) | B/L/K (in einigen Kreisen) | CC-BY 4.0 |
| **Thüringen** | TLBV – [Geoportal Thüringen](https://geoportal.thueringen.de/themen/verkehr) | **WFS + WMS** (Zählstellenbereiche + Verkehrsstärken) | SVZ 2015/2021 | A/B/L | dl-de/by-2.0 |

Legende Netz: A = Autobahn, B = Bundesstraße, L = Landes-/Staatsstraße, K = Kreisstraße.

---

## Einordnung nach Aufwand

**Gruppe 1 – maschinenlesbar per Geodienst (WFS/WMS/OGC API, je ~1 Adapter):**
Bayern, Berlin, Brandenburg, Hamburg, Niedersachsen, Rheinland-Pfalz, Sachsen, Saarland, Thüringen, Sachsen-Anhalt (Netz), Schleswig-Holstein, NRW (Shape/Atom). → hier zuerst ansetzen.

**Gruppe 1b – maschinenlesbar als Tabelle (Download/API, Geometrie per Join):**
Baden-Württemberg (Excel je Klasse, jahresweise 2010–2024, + CKAN-API; Join mit Zählstellen-Karte).

**Gruppe 2 – nur Viewer/PDF:**
Bremen (PDF, älter) und Hessen (Viewer/PDF, Herausgabe maschinenlesbarer Daten verweigert → UIG-Anfrage oder Verzicht). Für beide: A/B ohnehin über BASt abgedeckt.

---

## Bundesweiter Backbone (Fernstraßen, ergänzend)

- **BASt** – Einzelergebnisse der Zählstellen als **Excel mit X/Y-Koordinaten** (ETRS89/UTM32N), plus **Bundesfernstraßennetz als WFS** (ASB, CC-BY 4.0).
  - SVZ-Ergebnisse: <https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/Manuelle-Zaehlung.html>
  - Netz-WFS (Metadaten): <https://gdk.gdi-de.org/geonetwork/srv/api/records/4536A941-63DE-4C76-954B-F07109144DCB>
- Hinweis: Die BASt-Ergebnisse für A/B stecken i.d.R. schon in den Länderdaten. Der Mehrwert der Länderdaten liegt im **nachgeordneten Netz (L/K)**.

---

## Stolpersteine fürs gemeinsame Format

1. **Metrik:** DTV (Mo–So) vs. DTVw (Werktage) – nicht in dieselbe Skala werfen. Schwerverkehr mal als DTV-SV, mal als prozentualer Anteil.
2. **Bezugsjahr:** mischt 2015 / 2019 / 2021 / hochgerechnete Zwischenjahre.
3. **Geometriemodell:** Linien-Segmente (BE) vs. Punkt-Zählstellen (BW) vs. Zählstellenbereiche (BB/TH).
4. **CRS:** meist ETRS89/UTM 32N (EPSG:25832) bzw. 25833 (Ost) → nach WGS84 reprojizieren.
5. **Lizenz:** dl-de/zero (keine Nennung), dl-de/by-2.0 und CC-BY 4.0 (Quellenvermerk Pflicht) – Attribution mitführen.
6. **Pflege:** jedes Land aktualisiert eigenständig; SVZ-2025-Daten kommen gestaffelt ab Ende 2026.
