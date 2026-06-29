"""Gemeinsame Zugriffs-Bausteine für die Länder-Adapter.

Gruppiert nach den Zugangsarten aus der Quellen-Recherche (WFS / OGC API / ATOM /
ArcGIS / Excel). Ein Land-Adapter ist damit nur noch Verdrahtung: passenden Holer
aufrufen, dann `to_canonical(...)`. `fetch_arcgis_paginated` ist direkt aus
`unfallkarte.hvs` abgeleitet (resultOffset-Pagination, outSR=4326).

Konvention: Holer geben ein GeoDataFrame in EPSG:4326 zurück (Reprojektion macht
`to_canonical`, falls die Quelle in UTM liefert). `write_fgb` filtert Null-/leere
Geometrien — genau die FlatGeobuf-Falle aus `hvs.to_fgb`.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    import pandas as pd
    from geopandas import GeoDataFrame

from svzkarte import schema

_TIMEOUT = 180
_UA = {"User-Agent": "svzkarte/0.1 (+https://github.com/vizsim)"}


# --- OGC API Features (RLP /spatial-objects/393, moderne ldproxy-Endpunkte) ---
def fetch_ogc_features(
    base_url: str, collection: str, *, limit: int = 1000, crs_uri: str | None = None
) -> GeoDataFrame:
    """Paginiert `…/collections/<collection>/items` (GeoJSON) via rel=next-Links.

    `base_url` ist die Landing-Page des OGC-API-Dienstes (ohne /collections).
    """
    import geopandas as gpd

    url = f"{base_url.rstrip('/')}/collections/{collection}/items"
    params: dict[str, Any] = {"f": "json", "limit": limit}
    if crs_uri:
        params["crs"] = crs_uri
    feats: list[dict] = []
    session = requests.Session()
    session.headers.update(_UA)
    while url:
        r = session.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        doc = r.json()
        feats.extend(doc.get("features", []))
        url = next(
            (lnk["href"] for lnk in doc.get("links", []) if lnk.get("rel") == "next"), None
        )
        params = {}  # next-Link trägt die Query bereits
        print(f"    OGC {collection}: {len(feats)}")
    return gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")


# --- WFS (BY, SN, ST-Netz, SL, TH, BB, SH …) ---
def fetch_wfs(
    url: str, typename: str, *, bbox: str | None = None, version: str = "2.0.0"
) -> GeoDataFrame:
    """GetFeature gegen einen WFS, Ausgabe als GeoJSON, gelesen via geopandas.

    Viele Landesdienste sprechen WFS 2.0.0 + `outputFormat=application/json`. Wenn
    ein Dienst kein JSON kann, hier auf GML umstellen (pyogrio liest beides).
    """
    import geopandas as gpd

    params = {
        "service": "WFS",
        "version": version,
        "request": "GetFeature",
        "typeNames" if version >= "2.0.0" else "typeName": typename,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
    }
    if bbox:
        params["bbox"] = bbox
    r = requests.get(url, params=params, headers=_UA, timeout=_TIMEOUT)
    r.raise_for_status()
    return gpd.read_file(io.BytesIO(r.content))


# --- ATOM / INSPIRE-Downloaddienst (NI, NRW-Shape) ---
def fetch_atom(feed_url: str, *, match: str | None = None) -> GeoDataFrame:
    """Liest einen INSPIRE-Atom-Feed, lädt das (erste passende) verlinkte Dataset
    (GML/Shape/GeoJSON, ggf. gezippt) und gibt es als GeoDataFrame zurück.

    `match` filtert die Download-Links per Substring (z.B. Jahr oder 'Zaehlstellen').
    """
    import re

    import geopandas as gpd

    r = requests.get(feed_url, headers=_UA, timeout=_TIMEOUT)
    r.raise_for_status()
    hrefs = re.findall(r'href="([^"]+)"', r.text)
    cand = [h for h in hrefs if h.lower().endswith((".zip", ".gml", ".json", ".geojson"))]
    if match:
        cand = [h for h in cand if match.lower() in h.lower()]
    if not cand:
        raise ValueError(f"Atom-Feed {feed_url}: kein Download-Link (match={match!r})")
    data = requests.get(cand[0], headers=_UA, timeout=_TIMEOUT).content
    if cand[0].lower().endswith(".zip"):
        return _read_zip_vector(data)
    return gpd.read_file(io.BytesIO(data))


def _read_zip_vector(data: bytes) -> GeoDataFrame:
    import geopandas as gpd

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        inner = next(
            (n for n in zf.namelist() if n.lower().endswith((".shp", ".gml", ".geojson", ".json"))),
            None,
        )
        if inner is None:
            raise ValueError(f"ZIP ohne Vektordatei: {zf.namelist()}")
        # geopandas/pyogrio liest direkt aus dem ZIP via virtuellem Pfad.
        tmp = Path("/tmp") / inner
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(inner) as src, tmp.open("wb") as dst:
            dst.write(src.read())
        return gpd.read_file(tmp)


# --- ArcGIS FeatureServer/MapServer (BASt-/Hub-artige Dienste) ---
def fetch_arcgis_paginated(
    query_url: str, out_fields: str = "*", *, page: int = 2000, where: str = "1=1"
) -> GeoDataFrame:
    """resultOffset-Pagination gegen einen ArcGIS-`/query`-Endpunkt (outSR=4326).

    1:1-Muster aus `unfallkarte.hvs.fetch` (stabile orderByFields-Sortierung).
    """
    import geopandas as gpd

    session = requests.Session()
    session.headers.update(_UA)
    feats: list[dict] = []
    offset = 0
    while True:
        r = session.get(
            query_url,
            params={
                "where": where,
                "outFields": out_fields,
                "outSR": 4326,
                "orderByFields": "OBJECTID",
                "resultOffset": offset,
                "resultRecordCount": page,
                "returnGeometry": "true",
                "f": "geojson",
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        chunk = r.json().get("features", [])
        if not chunk:
            break
        feats.extend(chunk)
        offset += page
        print(f"    ArcGIS: {len(feats)}")
    return gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")


# --- Excel-Tabelle + Geometrie-Join (BW-Sonderfall) ---
def read_excel_zip(url: str, *, sheet: int | str = 0) -> pd.DataFrame:
    """Lädt ein (ggf. gezipptes) XLSX und gibt das Blatt als DataFrame zurück."""
    import pandas as pd

    data = requests.get(url, headers=_UA, timeout=_TIMEOUT).content
    if url.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            name = next(n for n in zf.namelist() if n.lower().endswith((".xlsx", ".xls")))
            data = zf.read(name)
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet)


def join_stations(
    df: pd.DataFrame, stations: GeoDataFrame, *, on: str
) -> GeoDataFrame:
    """Hängt die Geometrie aus der Zählstellen-Karte an die Wertetabelle (BW)."""
    import geopandas as gpd

    merged = stations[[on, "geometry"]].merge(df, on=on, how="inner")
    return gpd.GeoDataFrame(merged, geometry="geometry", crs=stations.crs)


# --- Mapping auf das kanonische Schema ---
def to_canonical(
    gdf: GeoDataFrame,
    mapping: dict[str, str],
    *,
    metric: str,
    year: int,
    state: str,
    source: str,
    license: str,
    road_class: str | None = None,
    road_class_from: str | None = None,
    road_class_map: dict[Any, str] | Callable[[Any], str] | None = None,
) -> GeoDataFrame:
    """Benennt Quellspalten um, setzt Konstanten, wirft Fremdspalten weg, reprojiziert
    nach EPSG:4326. Ergebnis erfüllt `schema.COLUMNS` (vor write_fgb/merge validierbar).

    `mapping` = {Quellspalte: kanonische Spalte} (nur die kanonischen Wertspalten:
    dtv_kfz/dtv_sv/sv_anteil/road_no/station_id). `road_class` setzt eine Konstante,
    `road_class_from`+optional `road_class_map` leitet sie je Zeile aus einer Spalte ab.
    """
    import geopandas as gpd

    out = gdf.rename(columns=mapping)

    if out.crs is not None and out.crs.to_epsg() != schema.EPSG:
        out = out.to_crs(epsg=schema.EPSG)

    out["metric"] = metric
    out["year"] = int(year)
    out["state"] = state
    out["source"] = source
    out["license"] = license

    if road_class is not None:
        out["road_class"] = road_class
    elif road_class_from is not None:
        col = out[road_class_from] if road_class_from in out.columns else gdf[road_class_from]
        if callable(road_class_map):
            out["road_class"] = col.map(road_class_map)
        elif road_class_map:
            out["road_class"] = col.map(road_class_map)
        else:
            out["road_class"] = col
    else:
        raise ValueError("road_class oder road_class_from angeben")

    for opt in ("dtv_kfz", "dtv_sv", "sv_anteil", "road_no", "station_id"):
        if opt not in out.columns:
            out[opt] = None

    keep = [*schema.COLUMNS, "geometry"]
    out = gpd.GeoDataFrame(out[keep], geometry="geometry", crs=f"EPSG:{schema.EPSG}")
    for intcol in ("dtv_kfz", "dtv_sv"):
        out[intcol] = out[intcol].astype("Int64")
    return out


# --- FlatGeobuf-Write (Null-/leere Geometrien filtern!) ---
def write_fgb(gdf: GeoDataFrame, path: Path) -> tuple[Path, int]:
    """Schreibt ein GeoDataFrame als FlatGeobuf; verwirft vorher Null-/leere
    Geometrien (sonst bricht der FlatGeobuf-Write ab — die `hvs`-Erfahrung).
    """
    clean = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean.to_file(path, driver="FlatGeobuf")
    return path, len(clean)
