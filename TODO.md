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
- **Mecklenburg-Vorpommern (MV)** — WFS/SVZ-Endpunkt noch nicht verifiziert (offen).
- **Bremen (HB) / Hessen (HE)** — nur PDF/Viewer, keine maschinenlesbaren Vektor-DTV.

Gemeinsamer Ausweg für all diese: der **BASt-Backbone** deckt A/B bundesweit ab; das
nachgeordnete Netz (L/K) bleibt bei diesen Ländern lückenhaft, bis eine DTV-Tabelle
(mit VNK/NNK oder Zählstellennr) auftaucht — dann Join wie bei ST/TH.

## Sonstiges
- Punkt-Quellen erledigt: BW + SL als eigener `svz_points`-Layer (Kreis-Layer im Frontend).
- Frontend: Filter-UI (Jahr / Bundesland / Klasse / Metrik DTV vs. DTVw getrennt).
- Datenkuriosum HH: ein BAB-Segment mit `dtv=1.240.000` (Quell-Ausreißer) – ggf. kappen.
- Deploy/CI noch offen (B2 vs. GitHub Pages/Release).
