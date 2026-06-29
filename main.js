// Verkehrsmengenkarte – MapLibre-Viewer für svz_de.pmtiles.
// Basemap: lokales OpenFreeMap-Positron-style.json (keyless). Die svz-Linien werden
// UNTER die erste Symbol-(Label-)Ebene gehängt -> Orts-/Straßennamen bleiben oben.
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

// Basemap: gehosteter OpenFreeMap-Positron-Style (keyless, kein lokales style.json).
const map = new maplibregl.Map({
  container: "map",
  style: "https://tiles.openfreemap.org/styles/positron",
  center: [13.404, 52.52],
  zoom: 10.3,
  hash: true,
  minZoom: 5,
  maxZoom: 18,
});
window.map = map;

map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");

map.on("load", () => {
  map.addSource("svz", {
    type: "vector",
    url: "pmtiles://" + PMTILES_URL,
    attribution: "Verkehrsmengen: Straßenbauverwaltungen der Länder",
  });

  // Beide Daten-Layer direkt unter die erste Symbol-(Label-)Ebene legen.
  const firstSymbol = map.getStyle().layers.find((l) => l.type === "symbol")?.id;

  // Linien-Länder (Zählstellenbereiche/Segmente).
  map.addLayer(
    {
      id: "svz-lines",
      type: "line",
      source: "svz",
      "source-layer": "svz",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": colorExpr,
        "line-opacity": 0.9,
        "line-width": [
          "interpolate", ["linear"], ["zoom"],
          6, 1.0, 9, 1.8, 13, 3.5, 16, 7,
        ],
      },
    },
    firstSymbol,
  );

  // Punkt-Länder (Zählstellen-Standorte, z.B. BW/SL) als Kreise.
  map.addLayer(
    {
      id: "svz-points",
      type: "circle",
      source: "svz",
      "source-layer": "svz_points",
      paint: {
        "circle-color": colorExpr,
        "circle-opacity": 0.9,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 0.7,
        "circle-radius": [
          "interpolate", ["linear"], ["zoom"],
          6, 2, 10, 4, 14, 7,
        ],
      },
    },
    firstSymbol,
  );

  // Klick-Popup + Cursor für beide Layer.
  const fmt = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"));
  const onClick = (e) => {
    const p = e.features[0].properties;
    const road = p.road_no || `${p.road_class}-Straße`;
    const sv =
      p.dtv_sv != null
        ? `<div class="popup-meta">davon SV: ${fmt(p.dtv_sv)}</div>`
        : p.sv_anteil != null
          ? `<div class="popup-meta">SV-Anteil: ${p.sv_anteil} %</div>`
          : "";
    new maplibregl.Popup({ closeButton: false })
      .setLngLat(e.lngLat)
      .setHTML(
        `<div class="popup-road">${road}</div>` +
        `<div class="popup-dtv">${fmt(p.dtv_kfz)} Kfz/24h <span class="popup-meta">(${p.metric})</span></div>` +
        sv +
        `<div class="popup-meta">Klasse ${p.road_class} · ${p.year} · ${p.state}</div>`,
      )
      .addTo(map);
  };
  for (const id of ["svz-lines", "svz-points"]) {
    map.on("click", id, onClick);
    map.on("mouseenter", id, () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", id, () => (map.getCanvas().style.cursor = ""));
  }
});

// Legende aus derselben Skala bauen.
const legend = document.getElementById("legend-scale");
const labels = ["0", "3 000", "8 000", "15 000", "25 000", "40 000", "60 000+"];
SCALE.forEach(([, color], i) => {
  const row = document.createElement("div");
  row.className = "legend-row";
  row.innerHTML = `<span class="legend-swatch" style="background:${color}"></span>${labels[i]}`;
  legend.appendChild(row);
});
