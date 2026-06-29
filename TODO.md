# TODO / offene Punkte

## Autobahn-Lücke bei BE und NRW (+ Inkonsistenz allgemein)

**Beobachtung** (Klassen-Verteilung je Land, Stand 6 Länder):

| Land | Autobahn-Segmente (A) |
|---|---|
| HH | 575 |
| BY | 490 |
| NI | 302 |
| BW | 170 |
| BB | 136 |
| **BE** | **10** (faktisch keine) |
| **NW** | **0** |

**Warum?** Autobahnen sind seit 01.01.2021 **Bundessache** – sie werden von der
**Autobahn GmbH des Bundes** verwaltet, nicht mehr von den Ländern. Deshalb
veröffentlichen mehrere Landes-SVZ-Datensätze **nur das nachgeordnete Netz**
(B/L/K + innerstädtische Hauptstraßen):
- **NRW** (`Verkehrswerte2019HR`) enthält ausschließlich B/L/K – Autobahnen fehlen ganz.
- **Berlin** liefert das städtische Hauptstraßennetz; nur ~10 A-Schnipsel (A100 etc.).
- **BY/NI/BB/HH/BW** führen BAB historisch in ihren SVZ mit → daher die Inkonsistenz.

**Lösung: BASt-Backbone ergänzen.** Die BASt (Bundesanstalt für Straßenwesen)
veröffentlicht die bundesweite manuelle Straßenverkehrszählung für **alle
Bundesfernstraßen (A + B)** mit DTV:
- Einzelergebnisse als **Excel mit X/Y-Koordinaten** (ETRS89/UTM32N) → Punkt-Quelle.
- **Bundesfernstraßennetz als WFS** (ASB, CC-BY 4.0) → Liniengeometrie.

Ein eigener `bast`-Adapter würde damit **lückenlose Autobahnen überall** liefern.
Wichtig dabei: BASt-A/B **überlappt** mit den Ländern, die A/B schon mitliefern →
Dedup-Strategie nötig. Sauberste Aufteilung (lt. Konzept): **BASt für A (ggf. B),
Länder fürs nachgeordnete Netz (L/K/G)** – verhindert Doppelzählung.

## Punkt-Quellen (in Arbeit)
- BW (`DTV2024`, mobidata-bw GeoJSON) und SL (`SVZ_Zaehlstellen`, ArcGIS-WFS) sind
  **Punkt**-Zählstellen → eigener `svz_points`-Layer (Pipeline + Frontend-Kreislayer).

## Sonstiges
- Frontend: Filter-UI (Jahr / Bundesland / Klasse / Metrik DTV vs. DTVw getrennt).
- Datenkuriosum HH: ein BAB-Segment mit `dtv=1.240.000` (Quell-Ausreißer) – ggf. kappen.
- Deploy/CI noch offen (B2 vs. GitHub Pages/Release).
- Offene Länder: TH, SH, ST, MV (WFS gesucht); SN/RP nur WMS (blockiert).
