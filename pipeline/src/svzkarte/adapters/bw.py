"""Baden-Württemberg: SVZ 2024, Zählstellen als PUNKTE (MobiData BW).

Live verifiziert (Sept. 2026): „Grunddaten hinter der SVZ-Karte BW" als CSV (5638 Zeilen,
Koordinaten gpsx1/gpsy1 in EPSG:4326) mit den augmentierten SVZ-2024-Werten. Felder:
DTV2024 (DTV Kfz), DTVSV, klasse (A/B/L/K), nummer (Straßennummer), svznr
(Zählstellennummer). DTV = alle Tage. Bis 09/2026 kam dieselbe Tabelle als GeoJSON
(`karten_geojsons/…_231011_…`, jetzt 404); die CSV (Stand 2026-06-26) trägt für alle 5597
gemeinsamen Zählstellen identische Werte, dazu +41/−32 Zählstellen und 112 korrigierte Lagen.
Der Dateiname enthält das Standdatum -> bei 404 im CKAN-Datensatz
`karte_strassenverkehrszaehlung` nach der neuen Ressource schauen.

Punkt-Quelle -> landet im merge in svz_points.fgb (eigener Frontend-Kreislayer).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svzkarte.adapters import base
from svzkarte.config import load_yaml

if TYPE_CHECKING:
    from geopandas import GeoDataFrame

_STATE = "BW"
_CODE = "bw"

FIELD_MAP = {            # Quell-Spalte -> kanonische Spalte
    "DTV2024": "dtv_kfz",
    "DTVSV": "dtv_sv",
    "svznr": "station_id",
    "road_no": "road_no",     # in normalize() aus klasse+nummer gebaut
}
_CLASS = {"A": "A", "B": "B", "L": "L", "K": "K"}


def _road_class(v: object) -> str:
    return _CLASS.get(str(v).strip(), "L")


def _cfg() -> dict:
    return load_yaml("sources.yaml")["sources"][_CODE]


def normalize() -> GeoDataFrame:
    """Zählstellen-CSV (Punkte aus gpsx1/gpsy1, EPSG:4326) -> kanonisches Schema."""
    cfg = _cfg()
    g = base.fetch_csv_points(cfg["url"], x="gpsx1", y="gpsy1").copy()
    # road_no aus Klasse + Nummer, z.B. "L 508".
    g["road_no"] = (
        g["klasse"].astype(str).str.strip() + " " + g["nummer"].astype(str).str.strip()
    )
    return base.to_canonical(
        g,
        mapping=FIELD_MAP,
        metric=cfg.get("metric", "DTV"),
        year=cfg["year"],
        road_class_from="klasse",
        road_class_map=_road_class,
        state=_STATE,
        source=_CODE,
        license=cfg["license"],
    )
