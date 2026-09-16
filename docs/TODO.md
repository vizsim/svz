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

**Lösung: BASt-Backbone — ✅ umgesetzt (A + B)** ([adapters/bast.py](pipeline/src/svzkarte/adapters/bast.py)).
Die BASt veröffentlicht die bundesweite SVZ der Bundesfernstraßen als Excel mit
**X/Y-Koordinaten** (ETRS89/UTM32N) → direkt als Punkte baubar. Integriert sind
`Autobahnen-2021.xlsx` + `Bundesstrassen-2021.xlsx` (Blatt „Zeilenformat", zusammen
**11.950 Zählstellen** mit Koordinaten) als Punkt-Quelle `bast` (`state=DE`,
`source=bast`) → füllt die A-Lücke bundesweit (v.a. NW/BE). Ausgespielt in ein
**eigenes `svz_bast.pmtiles`** (Layer `bast`), im Frontend per Toggle ein-/ausblendbar.

Offen:
- **Dedup**: BASt **überlappt** mit den Ländern, die A/B schon mitliefern (v.a. B ist
  bei allen Linien-Ländern dabei). Aktuell koexistieren beide, aber der BASt-Layer ist
  wegschaltbar. Saubere Aufteilung wäre: BASt für A/B, Länder fürs nachgeordnete Netz
  (L/K/G) — noch offen.
- Alternativ gäbe es das **Bundesfernstraßennetz als WFS** (Liniengeometrie) für eine
  Linien- statt Punktdarstellung.
- ✅ **Quellen-Panel** im Frontend gebaut (ausklappbar, pro Quelle ein-/ausblenden via
  state-Filter bzw. BASt-Visibility, „alle an/aus").

## Datenlücken & blockierte Länder (Doku der Recherche-Sackgassen)

Ein wiederkehrendes Muster: manche Länder veröffentlichen nur **Netzgeometrie**
(Straßennetz/Netzknoten) ohne DTV, oder die DTV nur als **PDF/Viewer** — dann fehlt
eine maschinenlesbare Werte-Tabelle zum Join.

- **Schleswig-Holstein (SH)** — WFS `WFS_SH_Strasseninfo` ist **nur Netzgeometrie**
  (`Strassennetz`/`Netzknoten`, Schlüssel VNK/NNK), **kein DTV-FeatureType**. Laut
  LBV.SH selbst (IFG-Antwort auf [FragDenStaat](https://fragdenstaat.de/anfrage/zaehlstellen-zaehlstellenkarte-verkehrsmengenkarte/)):
  nur **Bundesfernstraßen (A/B)** werden standardisiert ausgewertet; fürs **Landes-/
  Kreisnetz existiert KEINE maschinenlesbare DTV-Datenbank** (nur temporäre,
  unkalibrierte Messungen; Verkehrsmengenkarte nur 2015; Rest via BASt-Statistik).
  → L/K blockiert; A/B nur über den BASt-Backbone (s. oben).
- **Rheinland-Pfalz (RP)** — OGC API Features (`spatial-objects/393`, Collections
  `DTV_WFS:SVZ{Jahr}_Zaehlstellenbereiche`) existiert, liefert aber serverseitig
  konstant „Wfs object could not be created from db!" → warten, bis der Dienst läuft.
  Info-Portal (Viewer/PDF): <https://lbm.rlp.de/themen/strassendaten/verkehrsstaerkenkarten>.
- **Mecklenburg-Vorpommern (MV)** — WFS/SVZ-Endpunkt noch nicht verifiziert; als Info
  eine Verkehrsmengenkarte 2021 (PDF, LSBV M-V):
  <https://www.strassen-mv.de/static/LSBV/Dateien/Downloads/Verkehrsmengenkarten/vmk2021.pdf>.
- **Bremen (HB)** — nur PDF-Verkehrsmengenkarten:
  <https://bau.bremen.de/mobilitaet/verkehrsdaten/verkehrsmengenkarten-59016>.
- **Hessen (HE)** — nur interaktiver Viewer/PDF (maschinenlesbare Herausgabe verweigert):
  <https://mobil.hessen.de/verkehr/interaktive-verkehrsmengenkarte>.

Gemeinsamer Ausweg für all diese: der **BASt-Backbone** deckt A/B bundesweit ab; das
nachgeordnete Netz (L/K) bleibt bei diesen Ländern lückenhaft, bis eine DTV-Tabelle
(mit VNK/NNK oder Zählstellennr) auftaucht — dann Join wie bei ST/TH.

## Kommunale Daten (Ebene 3, Issue #1)

Konzept + Stand: [Konzept_kommunale_daten.md](Konzept_kommunale_daten.md). Umgesetzt:
Köln, Düsseldorf (Linien), Ravensburg, Weingarten, Berg, Baienfurt, Baindt (Punkte,
24h) in `svz_kommunal.pmtiles`; Panel nach Ebenen gruppiert, Hinzoomen, Übersichts-Marker.
Lausitz (DiSTILL) geprüft und verworfen (identisch mit bb/sn). Offen:
- **Frankfurt** (HE): WFS liefert 500 → regelmäßig prüfen (`status: research`).
- **Rad/Fuß** aus den MobiData-Excels (optionale Spalten `dtv_rad`/`dtv_fuss` + Legenden-Modus)
  – vom Nutzer vorerst zurückgestellt.
- **Eigener Stil für `metric=24h`** (Einzelzählung ≠ DTV), z.B. gestrichelt.
- **SV Ravensburg/Weingarten** auffällig hoch (Median 14–18 %) – Definition beim Amt erfragen.
- **Dedup Kommune ↔ Land** im Stadtgebiet (Köln/Düsseldorf über NRW-Linien) – räumlicher
  Clip oder Vorrangregel.
- Dresden: WFS-Knoten des Themenstadtplan-Themas `STA_VERKEHRSMENGEN` finden.
- Panel-Optionen ab ~15 Kommunen: Gruppe zugeklappt, „nur im Ausschnitt", Suchfeld.

## Sonstiges
- Punkt-Quellen erledigt: BW + SL als eigener `svz_points`-Layer (Kreis-Layer im Frontend).
- Frontend: Filter-UI (Jahr / Bundesland / Klasse / Metrik DTV vs. DTVw getrennt).
- Datenkuriosum HH: ein BAB-Segment mit `dtv=1.240.000` (Quell-Ausreißer) – ggf. kappen.
- Deploy/CI noch offen (B2 vs. GitHub Pages/Release).
