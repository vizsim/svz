"""Kommunale Adapter: je Stadt `normalize() -> GeoDataFrame` (kanonisches Schema).

Gleiche Bausteine wie die Länder (`adapters/base.py`), aber `level="kommune"`,
`state` = Bundesland der Stadt, `source` = Stadt-Schlüssel aus sources.yaml (z.B.
`ravensburg`). Typische Eigenheiten kommunaler Quellen, die hier gelöst werden:
  - Einzelzählungen statt Jahresmittel (metric "24h"), Jahr je Zählstelle (year_from)
  - keine Straßenklasse -> "G" (städtisches Netz), dafür `name` (Knoten/Straße)
  - Werte je Richtung/Jahr in Spaltenblöcken (Köln) oder wiederholten Blöcken (Ravensburg)
"""
