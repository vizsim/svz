// Verkehrsmengenkarte – MapLibre-Viewer.
// Basemap: gehostetes OpenFreeMap-Positron. Daten in ZWEI PMTiles/Quellen:
//   svz  = Länder (Layer `svz` Linien + `svz_points` Punkte)
//   bast = bundesweiter BASt-Backbone (Layer `bast`, A+B), separat schaltbar.
// Alle Daten-Layer hängen UNTER der ersten Symbol-(Label-)Ebene -> Labels oben.
const PMTILES_URL = "pipeline/data/svz/svz_de.pmtiles";
const BAST_PMTILES_URL = "pipeline/data/svz/svz_bast.pmtiles";
// UBA-Hauptverkehrsstraßen (END 2021, bundesweit) – gehostet aus unfallkarte, als
// Fallback/Backbone. Attribut annualTrafficFlow (Kfz/Jahr), Layer `lines`.
const HVS_PMTILES_URL =
  "https://tiles.vizsim.de/file/unfallkarte-data-v2/uba/hvs_verkehrsmengen.pmtiles";

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

// Lizenz-Kürzel -> Volltext-URL (für den Hyperlink im Panel).
const LICENSES = {
  "dl-de/by-2.0": "https://www.govdata.de/dl-de/by-2-0",
  "dl-de/zero-2.0": "https://www.govdata.de/dl-de/zero-2-0",
  "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
  offen: null,
};

// Quellen für das Panel (Reihenfolge = Anzeige). `code` = state-Feld in den Daten;
// `kind` steuert das Toggle: Länder filtern die geteilten Layer nach state, BASt ist
// ein eigener Layer (Visibility). Berlin ist DTVw (nur Werktage).
const SOURCES = [
  { code: "BW", name: "Baden-Württemberg", year: 2024, metric: "DTV", license: "dl-de/by-2.0", kind: "land" },
  { code: "BY", name: "Bayern", year: 2021, metric: "DTV", license: "CC-BY-4.0", kind: "land" },
  { code: "BE", name: "Berlin", year: 2023, metric: "DTVw", license: "dl-de/zero-2.0", kind: "land" },
  { code: "BB", name: "Brandenburg", year: 2021, metric: "DTV", license: "dl-de/by-2.0", kind: "land" },
  { code: "HH", name: "Hamburg", year: 2019, metric: "DTV", license: "dl-de/by-2.0", kind: "land" },
  { code: "NI", name: "Niedersachsen", year: 2021, metric: "DTV", license: "CC-BY-4.0", kind: "land" },
  { code: "NW", name: "Nordrhein-Westfalen", year: 2019, metric: "DTV", license: "dl-de/by-2.0", kind: "land" },
  { code: "SL", name: "Saarland", year: 2021, metric: "DTV", license: "CC-BY-4.0", kind: "land" },
  { code: "SN", name: "Sachsen", year: 2021, metric: "DTV", license: "dl-de/by-2.0", kind: "land" },
  { code: "ST", name: "Sachsen-Anhalt", year: 2021, metric: "DTV", license: "dl-de/by-2.0", kind: "land" },
  { code: "TH", name: "Thüringen", year: 2015, metric: "DTV", license: "dl-de/by-2.0", kind: "land" },
  { code: "DE", name: "BASt-Backbone (A+B)", year: 2021, metric: "DTV", license: "© BASt", kind: "bast", layer: "bast-points" },
  { code: "HVS", name: "UBA-Hauptverkehrsstraßen", year: 2021, metric: "DTV≈", license: "© UBA", kind: "hvs", layer: "hvs-lines", default: false, minZoom: 9, hint: "nur Straßen > 3 Mio Kfz/Jahr" },
];

// pmtiles-Protokoll registrieren.
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

// dtv_kfz -> Farbe. Fehlt der Wert (keine Zählung), NICHT als 0 einfärben, sondern grau.
const NODATA = "#b4b4b4";
const interp = ["interpolate", ["linear"], ["get", "dtv_kfz"]];
for (const [v, c] of SCALE) interp.push(v, c);
const colorExpr = ["case", ["has", "dtv_kfz"], interp, NODATA];

// UBA-HVS trägt annualTrafficFlow (Kfz/Jahr) -> als DTV-Äquivalent (÷365) einfärben.
const hvsInterp = ["interpolate", ["linear"], ["/", ["to-number", ["get", "annualTrafficFlow"]], 365]];
for (const [v, c] of SCALE) hvsInterp.push(v, c);
const hvsColorExpr = ["case", ["has", "annualTrafficFlow"], hvsInterp, NODATA];

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

// --- Quellen-Panel (Tabelle: Land · Jahr · Metrik · Lizenz; ein-/ausblenden je Quelle) ---
const srcAll = document.getElementById("src-all");
const srcList = document.getElementById("sources-list");        // Länder
const srcBastBody = document.getElementById("sources-bast-body"); // BASt, abgesetzt

const licenseCell = (code) => {
  const url = LICENSES[code];
  return url
    ? `<a href="${url}" target="_blank" rel="noopener">${code}</a>`
    : `<span class="src-lic-plain">${code}</span>`;
};

for (const s of SOURCES) {
  const tr = document.createElement("tr");
  tr.className = "src-row";
  tr.innerHTML =
    `<td><input type="checkbox" checked></td>` +
    `<td class="src-name">${s.name}</td>` +
    `<td class="src-year">${s.year}</td>` +
    `<td class="src-metric">${s.metric}</td>` +
    `<td class="src-lic">${licenseCell(s.license)}</td>`;
  const cb = tr.querySelector("input");
  cb.checked = s.default !== false; // HVS startet ausgeblendet (default:false)
  s.el = cb;
  cb.addEventListener("change", applySources);
  tr.addEventListener("click", (e) => {
    if (e.target.closest("a") || e.target === cb) return; // Lizenz-Link/Checkbox nicht abfangen
    cb.checked = !cb.checked;
    applySources();
  });
  const parent = s.kind === "land" ? srcList : srcBastBody; // Backbones (BASt, HVS) unten
  parent.append(tr);
  if (s.hint) {
    const ht = document.createElement("tr");
    ht.className = "src-hint";
    ht.innerHTML = `<td colspan="5"></td>`;
    parent.append(ht);
    s.hintEl = ht;
  }
}

srcAll.addEventListener("change", () => {
  for (const s of SOURCES) s.el.checked = srcAll.checked;
  applySources();
});

// Ein-/Ausklappen des Panels.
const srcToggle = document.getElementById("sources-toggle");
const srcBody = document.getElementById("sources-body");
srcToggle.addEventListener("click", () => {
  const open = srcBody.style.display !== "none";
  srcBody.style.display = open ? "none" : "block";
  srcToggle.textContent = open ? "Quellen ▸" : "Quellen ▾";
  srcToggle.setAttribute("aria-expanded", String(!open));
});

// Länder filtern die geteilten Layer nach `state`; BASt schaltet seinen eigenen Layer.
function applySources() {
  const states = SOURCES.filter((s) => s.kind === "land" && s.el.checked).map((s) => s.code);
  const filt = ["in", ["get", "state"], ["literal", states]];
  for (const id of ["svz-lines", "svz-points"]) {
    if (map.getLayer(id)) map.setFilter(id, filt);
  }
  // Backbone-Layer (BASt-Punkte, UBA-HVS-Linien) je Checkbox schalten.
  for (const s of SOURCES) {
    if (s.layer && map.getLayer(s.layer)) {
      map.setLayoutProperty(s.layer, "visibility", s.el.checked ? "visible" : "none");
    }
  }
  const all = SOURCES.every((s) => s.el.checked);
  srcAll.checked = all;
  srcAll.indeterminate = !all && SOURCES.some((s) => s.el.checked);
}

// Hinweis unter einer Quelle: dauerhaft `hint`; bei Zoom < minZoom zusätzlich der
// „erst ab Zoom N"-Vorsatz (z.B. UBA-HVS: nur >3 Mio Kfz/Jahr, erst ab Zoom 9).
function updateZoomHints() {
  for (const s of SOURCES) {
    if (!s.hintEl) continue;
    const prefix = s.minZoom && map.getZoom() < s.minZoom ? `erst ab Zoom ${s.minZoom} · ` : "";
    s.hintEl.querySelector("td").textContent = prefix + (s.hint || "");
  }
}
map.on("zoom", updateZoomHints);
updateZoomHints();

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

  // BASt-Backbone (Bundesfernstraßen A+B) als eigene Quelle/Layer -> separat schaltbar.
  map.addSource("bast", {
    type: "vector",
    url: "pmtiles://" + BAST_PMTILES_URL,
    attribution: "Bundesfernstraßen: © BASt",
  });
  map.addLayer(
    {
      id: "bast-points",
      type: "circle",
      source: "bast",
      "source-layer": "bast",
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

  // UBA-Hauptverkehrsstraßen (bundesweit, END 2021) als Fallback/Backbone — eigene,
  // gehostete Quelle, initial aus. Unter die Länder-Linien gelegt (Länderdaten oben).
  map.addSource("hvs", {
    type: "vector",
    url: "pmtiles://" + HVS_PMTILES_URL,
    attribution:
      'Hauptverkehrsstraßen: © <a href="https://gis.uba.de/maps/resources/apps/laermkartierung/index.html?lang=de" target="_blank" rel="noopener">UBA</a> (END 2021)',
  });
  map.addLayer(
    {
      id: "hvs-lines",
      type: "line",
      source: "hvs",
      "source-layer": "lines",
      layout: { "line-cap": "round", "line-join": "round", visibility: "none" },
      paint: {
        "line-color": hvsColorExpr,
        "line-opacity": 0.9,
        "line-width": [
          "interpolate", ["linear"], ["zoom"],
          6, 1.0, 9, 1.8, 13, 3.5, 16, 7,
        ],
      },
    },
    "svz-lines",
  );

  // Initiale Quellen-Sichtbarkeit setzen (Layer existieren jetzt).
  applySources();

  // Klick-Popup + Cursor für alle Daten-Layer.
  const fmt = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"));
  const onClick = (e) => {
    const p = e.features[0].properties;
    // UBA-Hauptverkehrsstraßen: annualTrafficFlow (Kfz/Jahr) -> DTV-Äquivalent (÷365).
    if (p.annualTrafficFlow != null) {
      const flow = Number(p.annualTrafficFlow);
      new maplibregl.Popup({ closeButton: false })
        .setLngLat(e.lngLat)
        .setHTML(
          `<div class="popup-road">Hauptverkehrsstraße</div>` +
          `<div class="popup-dtv">${fmt(Math.round(flow / 365))} Kfz/24h <span class="popup-meta">(DTV≈)</span></div>` +
          `<div class="popup-meta">${fmt(flow)} Kfz/Jahr · © UBA · END 2021</div>`,
        )
        .addTo(map);
      return;
    }
    const road = p.road_no || `${p.road_class}-Straße`;
    const sv =
      p.dtv_sv != null
        ? `<div class="popup-meta">davon SV: ${fmt(p.dtv_sv)}</div>`
        : p.sv_anteil != null
          ? `<div class="popup-meta">SV-Anteil: ${p.sv_anteil} %</div>`
          : "";
    const dtvLine =
      p.dtv_kfz != null
        ? `<div class="popup-dtv">${fmt(p.dtv_kfz)} Kfz/24h <span class="popup-meta">(${p.metric})</span></div>`
        : `<div class="popup-meta">keine DTV-Angabe (${p.metric})</div>`;
    new maplibregl.Popup({ closeButton: false })
      .setLngLat(e.lngLat)
      .setHTML(
        `<div class="popup-road">${road}</div>` +
        dtvLine +
        sv +
        `<div class="popup-meta">Klasse ${p.road_class} · ${p.year} · ${p.state}</div>`,
      )
      .addTo(map);
  };
  for (const id of ["svz-lines", "svz-points", "bast-points", "hvs-lines"]) {
    map.on("click", id, onClick);
    map.on("mouseenter", id, () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", id, () => (map.getCanvas().style.cursor = ""));
  }
});

// Legende aus derselben Skala bauen.
const legend = document.getElementById("legend-scale");
const labels = ["0", "3 000", "8 000", "15 000", "25 000", "40 000", "60 000+"];
const legendRows = [];
SCALE.forEach(([value, color], i) => {
  const row = document.createElement("div");
  row.className = "legend-row";
  row.innerHTML =
    `<span class="legend-swatch" style="background:${color}"></span>` +
    `<span class="legend-label">${labels[i]}</span>`;
  legend.appendChild(row);
  legendRows.push({ el: row, value });
});
const ndRow = document.createElement("div");
ndRow.className = "legend-row";
ndRow.innerHTML =
  `<span class="legend-swatch" style="background:${NODATA}"></span>` +
  `<span class="legend-label">keine Angabe</span>`;
legend.appendChild(ndRow);

// Dynamischer Hinweis auf den Zoom-Filter (DTV-Leiter, s. tiles.yaml).
const cut = document.createElement("div");
cut.id = "legend-cut";
legend.appendChild(cut);

// Schwelle je (Ganzzahl-)Zoom – muss zur DTV-Leiter in tiles.yaml passen.
function zoomThreshold(z) {
  const fz = Math.floor(z);
  if (fz >= 8) return 0;
  if (fz === 7) return 1000;
  if (fz === 6) return 2000;
  return 10000;
}

// Ausgefilterte Bereiche in der Legende ausgrauen + Schwelle anzeigen.
function updateLegendForZoom() {
  const t = zoomThreshold(map.getZoom());
  for (const { el, value } of legendRows) el.classList.toggle("dimmed", value < t);
  ndRow.classList.toggle("dimmed", t > 0); // Features ohne DTV erst ab Zoom 8
  if (t > 0) {
    cut.textContent = `bei diesem Zoom erst ab ${t.toLocaleString("de-DE")} Kfz/24h`;
    cut.style.display = "block";
  } else {
    cut.style.display = "none";
  }
}
map.on("zoom", updateLegendForZoom);
updateLegendForZoom();
