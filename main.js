// Verkehrsmengenkarte – MapLibre-Viewer für svz_de.pmtiles.
// Eine Source `svz` (PMTiles) + ein Linien-Layer, eingefärbt nach dtv_kfz.
// PMTILES_URL ist relativ zum ausgelieferten Root (lokal: über den Dev-Server).
const PMTILES_URL = "pipeline/data/svz/svz_de.pmtiles";

// Farbskala: niedrig (grün) -> hoch (rot). Ein Array für Layer-Paint UND Legende.
const SCALE = [
  [0, "#1a9850"],
  [3000, "#66bd63"],
  [8000, "#d9ef8b"],
  [15000, "#fee08b"],
  [25000, "#fdae61"],
  [40000, "#f46d43"],
  [60000, "#d73027"],
];

// pmtiles-Protokoll registrieren.
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

// dtv_kfz -> Farbe (interpolate). null/0 fällt auf den untersten Stop.
const colorExpr = ["interpolate", ["linear"], ["coalesce", ["get", "dtv_kfz"], 0]];
for (const [v, c] of SCALE) colorExpr.push(v, c);

const map = new maplibregl.Map({
  container: "map",
  center: [13.404, 52.52],
  zoom: 10.3,
  hash: true,
  style: {
    version: 8,
    glyphs: "https://basemaps.cartocdn.com/fonts/{fontstack}/{range}.pbf",
    sources: {
      basemap: {
        type: "raster",
        tiles: ["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "© OpenStreetMap, © CARTO",
      },
      svz: {
        type: "vector",
        url: "pmtiles://" + PMTILES_URL,
        attribution: "Verkehrsmengen: Straßenbauverwaltungen der Länder",
      },
    },
    layers: [
      { id: "basemap", type: "raster", source: "basemap" },
      {
        id: "svz-lines",
        type: "line",
        source: "svz",
        "source-layer": "svz",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": colorExpr,
          "line-opacity": 0.85,
          "line-width": [
            "interpolate", ["linear"], ["zoom"],
            6, 1.0, 9, 1.8, 13, 3.5, 16, 7,
          ],
        },
      },
    ],
  },
});

map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");

// Klick-Popup: road_no · DTV · year · state · Klasse.
const fmt = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"));
map.on("click", "svz-lines", (e) => {
  const p = e.features[0].properties;
  const road = p.road_no || `${p.road_class}-Straße`;
  new maplibregl.Popup({ closeButton: false })
    .setLngLat(e.lngLat)
    .setHTML(
      `<div class="popup-road">${road}</div>` +
      `<div class="popup-dtv">${fmt(p.dtv_kfz)} Kfz/24h <span class="popup-meta">(${p.metric})</span></div>` +
      (p.dtv_sv != null ? `<div class="popup-meta">davon SV: ${fmt(p.dtv_sv)}</div>` : "") +
      `<div class="popup-meta">Klasse ${p.road_class} · ${p.year} · ${p.state}</div>` +
      `<div class="popup-meta">ZSt ${p.station_id ?? "–"}</div>`
    )
    .addTo(map);
});
map.on("mouseenter", "svz-lines", () => (map.getCanvas().style.cursor = "pointer"));
map.on("mouseleave", "svz-lines", () => (map.getCanvas().style.cursor = ""));

// Legende aus derselben Skala bauen.
const legend = document.getElementById("legend-scale");
const labels = ["0", "3 000", "8 000", "15 000", "25 000", "40 000", "60 000+"];
SCALE.forEach(([, color], i) => {
  const row = document.createElement("div");
  row.className = "legend-row";
  row.innerHTML = `<span class="legend-swatch" style="background:${color}"></span>${labels[i]}`;
  legend.appendChild(row);
});

// Für den Headless-Screenshot: Flag setzen, sobald die Karte fertig gerendert ist.
map.on("idle", () => { window.__MAP_IDLE__ = true; document.title = "READY"; });
