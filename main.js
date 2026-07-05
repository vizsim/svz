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
// `access` = README-Spalte „Zugang (URL)": Format-Label(s) + Endpunkt-URL (mehrere
// Quellen je Land -> mehrere Einträge, im Panel mit „ · " getrennt verlinkt).
const SOURCES = [
  { code: "BW", name: "Baden-Württemberg", year: 2024, metric: "DTV", license: "dl-de/by-2.0", kind: "land",
    access: [{ l: "GeoJSON", u: "https://mobidata-bw.de/karten_geojsons/maps/count_car/SVZ-Zaehlstellen_231011_augmented_SVZ2024.geojson" }] },
  { code: "BY", name: "Bayern", year: 2021, metric: "DTV", license: "CC-BY-4.0", kind: "land",
    access: [{ l: "WFS", u: "https://gisportal-stmb.bayern.de/server/services/WFS/BAYSIS_Verkehrsdaten/MapServer/WFSServer" }] },
  { code: "BE", name: "Berlin", year: 2023, metric: "DTVw", license: "dl-de/zero-2.0", kind: "land",
    access: [{ l: "WFS", u: "https://gdi.berlin.de/services/wfs/verkehrsmengen_2023" }] },
  { code: "BB", name: "Brandenburg", year: 2021, metric: "DTV", license: "dl-de/by-2.0", kind: "land",
    access: [{ l: "WFS", u: "https://inspire.brandenburg.de/services/zaehlstellen_wfs" }] },
  { code: "HH", name: "Hamburg", year: 2019, metric: "DTV", license: "dl-de/by-2.0", kind: "land",
    access: [{ l: "WFS", u: "https://geodienste.hamburg.de/HH_WFS_Verkehrsmengen" }] },
  { code: "NI", name: "Niedersachsen", year: 2021, metric: "DTV", license: "CC-BY-4.0", kind: "land",
    access: [{ l: "ZIP", u: "https://map.strassenbau.niedersachsen.de/zip/DE-NI-SBV_Downloadservice_SVZ_Zaehlstellenbereiche_2021.zip" }] },
  { code: "NW", name: "Nordrhein-Westfalen", year: 2019, metric: "DTV", license: "dl-de/by-2.0", kind: "land",
    access: [{ l: "ZIP", u: "https://www.opengeodata.nrw.de/produkte/transport_verkehr/strassennetz/Verkehrswerte2019HR_EPSG25832_Shape.zip" }] },
  { code: "SL", name: "Saarland", year: 2021, metric: "DTV", license: "CC-BY-4.0", kind: "land",
    access: [{ l: "WFS", u: "https://geoportal.saarland.de/arcgis/services/Internet/Verkehr_WFS/MapServer/WFSServer" }] },
  { code: "SN", name: "Sachsen", year: 2021, metric: "DTV", license: "dl-de/by-2.0", kind: "land",
    access: [{ l: "ZIP", u: "https://www.list.smwa.sachsen.de/gdi/download/DE-SN-SBV-SVZ2021.zip" }] },
  { code: "ST", name: "Sachsen-Anhalt", year: 2021, metric: "DTV", license: "dl-de/by-2.0", kind: "land",
    access: [{ l: "WFS", u: "https://www.geodatenportal.sachsen-anhalt.de/gfds/ws/wfs/a78d7bc1-ffbb-cf76/GDI-LSA_LSBB_STRASSENNETZE/ows.wfs" }, { l: "Excel", u: "https://lsbb.sachsen-anhalt.de/fileadmin/Bibliothek/Politik_und_Verwaltung/Landesbetriebe/LSBB/Service/Strassenverkehrszaehlungen/Dateien_2025/Ergebnisse_SVZ_2021.xlsx" }] },
  { code: "TH", name: "Thüringen", year: 2015, metric: "DTV", license: "dl-de/by-2.0", kind: "land",
    access: [{ l: "WFS", u: "https://www.geoproxy.geoportal-th.de/geoproxy/services/STRNETZ_SVZ_wfs" }] },
  { code: "DE", name: "BASt-Backbone (A+B)", year: 2021, metric: "DTV", license: "© BASt", kind: "bast", layer: "bast-points",
    access: [{ l: "Excel A", u: "https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/2021/Autobahnen-2021.xlsx?__blob=publicationFile&v=1" }, { l: "Excel B", u: "https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/2021/Bundesstrassen-2021.xlsx?__blob=publicationFile&v=1" }] },
  { code: "HVS", name: "UBA-Hauptverkehrsstraßen", year: 2021, metric: "DTV≈", license: "© UBA", kind: "hvs", layer: "hvs-lines", default: false, minZoom: 9, hint: "nur Straßen > 3 Mio Kfz/Jahr",
    access: [{ l: "Viewer", u: "https://gis.uba.de/maps/resources/apps/laermkartierung/index.html?lang=de" }] },
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

// Zweite Färbung: SV-Anteil (% Schwerverkehr), umschaltbar per Legenden-Toggle.
const SCALE_SV = [
  [0, "#1a9850"],
  [5, "#66bd63"],
  [10, "#d9ef8b"],
  [15, "#fee08b"],
  [20, "#fdae61"],
  [25, "#f46d43"],
  [30, "#d73027"],
];
// SV-Anteil je Feature: direkt sv_anteil (%), sonst aus dtv_sv/dtv_kfz berechnet.
const svShare = [
  "case",
  ["has", "sv_anteil"], ["to-number", ["get", "sv_anteil"]],
  ["*", ["/", ["to-number", ["get", "dtv_sv"]], ["to-number", ["get", "dtv_kfz"]]], 100],
];
const svInterp = ["interpolate", ["linear"], svShare];
for (const [v, c] of SCALE_SV) svInterp.push(v, c);
// grau, wenn weder Anteil noch (SV & DTV>0) vorliegt.
const hasSv = [
  "any",
  ["has", "sv_anteil"],
  ["all", ["has", "dtv_sv"], ["has", "dtv_kfz"], [">", ["to-number", ["get", "dtv_kfz"]], 0]],
];
const svColorExpr = ["case", hasSv, svInterp, NODATA];

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

// „Zugang"-Zelle: Format-Label(s) als Links zum Endpunkt, mehrere mit „ · " getrennt.
const accessCell = (items = []) =>
  items
    .map((a) => `<a href="${a.u}" target="_blank" rel="noopener">${a.l}</a>`)
    .join('<span class="sep"> · </span>');

for (const s of SOURCES) {
  const tr = document.createElement("tr");
  tr.className = "src-row";
  tr.innerHTML =
    `<td><input type="checkbox" checked></td>` +
    `<td class="src-name">${s.name}</td>` +
    `<td class="src-year">${s.year}</td>` +
    `<td class="src-lic">${licenseCell(s.license)}</td>` +
    `<td class="src-access">${accessCell(s.access)}</td>`;
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

// Auf schmalen Screens (Handy) initial eingeklappt, damit die Karte sichtbar bleibt.
if (window.matchMedia("(max-width: 640px)").matches) {
  srcBody.style.display = "none";
  srcToggle.textContent = "Quellen ▸";
  srcToggle.setAttribute("aria-expanded", "false");
}

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
  updateZoomHints(); // Hinweiszeilen an den (Un)Check-Zustand anpassen
}

// Hinweis unter einer Quelle: dauerhaft `hint`; bei Zoom < minZoom zusätzlich der
// „erst ab Zoom N"-Vorsatz (z.B. UBA-HVS: nur >3 Mio Kfz/Jahr, erst ab Zoom 9).
function updateZoomHints() {
  for (const s of SOURCES) {
    if (!s.hintEl) continue;
    if (!s.el.checked) {
      s.hintEl.style.display = "none"; // Hinweis nur bei aktivierter Quelle
      continue;
    }
    s.hintEl.style.display = "";
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
    attribution:
      'Verkehrsmengen: <a href="https://github.com/vizsim/svz#datenquellen-der-16-bundesl%C3%A4nder" target="_blank" rel="noopener">Straßenbauverwaltungen der Länder</a>',
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
    attribution:
      'Bundesfernstraßen: © <a href="https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/Manuelle-Zaehlung.html" target="_blank" rel="noopener">BASt</a>',
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
      'Hauptverkehrsstraßen: © <a href="https://gis.uba.de/maps/resources/apps/laermkartierung/index.html?lang=de" target="_blank" rel="noopener">UBA</a>',
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
  const pct = (num, den) =>
    den ? ((Number(num) / Number(den)) * 100).toLocaleString("de-DE", { maximumFractionDigits: 1 }) : null;

  // Straßenklasse-Kürzel -> Klartext; Quelle „DE" = bundesweiter BASt-Backbone.
  const ROAD_CLASS = { A: "Autobahn", B: "Bundesstraße", L: "Landesstraße", K: "Kreisstraße", G: "Gemeindestraße" };
  const providerLabel = (state) => (state === "DE" ? "BASt" : state);

  // Metrik-Badge mit Erklär-Tooltip (hover) – DTV/DTVw/DTV≈ ausgeschrieben.
  const METRIC_TITLE = {
    DTV: "Durchschnittliche tägliche Verkehrsstärke (Kfz/24h, alle Tage)",
    DTVw: "Durchschnittliche tägliche Verkehrsstärke werktags (Mo–Fr)",
    "DTV≈": "Näherung aus Jahresmenge: Kfz/Jahr ÷ 365",
  };
  const metricBadge = (m) => `<span class="popup-metric" title="${METRIC_TITLE[m] || ""}">${m}</span>`;

  // „SV" = Schwerverkehr; Label mit Erklär-Tooltip beim Hovern.
  const svLabel = (t) => `<span class="popup-hint" title="Schwerverkehr: Lkw, Lastzüge, Busse (Kfz > 3,5 t)">${t}</span>`;

  // „Hero"-Zeile: große Zahl + gedämpfte Einheit + Metrik-Badge.
  const dtvHero = (val, metric) =>
    `<div class="popup-dtv">${fmt(val)} <span class="popup-unit">Kfz/24h</span> ${metricBadge(metric)}</div>`;

  const popup = (lngLat, html) =>
    new maplibregl.Popup({ closeButton: false, maxWidth: "270px" })
      .setLngLat(lngLat)
      .setHTML(html)
      .addTo(map);

  const onClick = (e) => {
    const p = e.features[0].properties;
    // UBA-Hauptverkehrsstraßen: annualTrafficFlow (Kfz/Jahr) -> DTV-Äquivalent (÷365).
    if (p.annualTrafficFlow != null) {
      const flow = Number(p.annualTrafficFlow);
      popup(
        e.lngLat,
        `<div class="popup-road">Hauptverkehrsstraße</div>` +
          dtvHero(Math.round(flow / 365), "DTV≈") +
          `<div class="popup-meta">${fmt(flow)} Kfz/Jahr · © UBA · END 2021</div>`,
      );
      return;
    }
    const road = p.road_no || `${p.road_class}-Straße`;
    const klass = ROAD_CLASS[p.road_class] || `Klasse ${p.road_class}`;

    // Schwerverkehr: absolut (+ berechneter Anteil) ODER nur Anteil %.
    let sv = "";
    if (p.dtv_sv != null) {
      const share = pct(p.dtv_sv, p.dtv_kfz);
      sv = `<div class="popup-sv">${svLabel("SV")} ${fmt(p.dtv_sv)}${share ? ` · ${share} %` : ""}</div>`;
    } else if (p.sv_anteil != null) {
      sv = `<div class="popup-sv">${svLabel("SV-Anteil")} ${p.sv_anteil} %</div>`;
    }

    const dtvLine =
      p.dtv_kfz != null
        ? dtvHero(p.dtv_kfz, p.metric)
        : `<div class="popup-meta">keine DTV-Angabe ${metricBadge(p.metric)}</div>`;

    popup(
      e.lngLat,
      `<div class="popup-road">${road}</div>` +
        dtvLine +
        sv +
        `<div class="popup-meta">${klass} · ${p.year} · ${providerLabel(p.state)}</div>`,
    );
  };
  for (const id of ["svz-lines", "svz-points", "bast-points", "hvs-lines"]) {
    map.on("click", id, onClick);
    map.on("mouseenter", id, () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", id, () => (map.getCanvas().style.cursor = ""));
  }
});

// --- Legende: umschaltbar DTV <-> SV-Anteil (Modus-Toggle im Legenden-Kopf). ---
const legend = document.getElementById("legend-scale");
const legendTitle = document.getElementById("legend-title");
const DTV_LABELS = ["0", "3 000", "8 000", "15 000", "25 000", "40 000", "60 000+"];
const SV_LABELS = ["0", "5", "10", "15", "20", "25", "30+"]; // % Schwerverkehr

let mode = "dtv";     // aktive Färbung: "dtv" | "sv"
let legendRows = [];  // pro Modus neu aufgebaut
let ndRow, cut;       // "keine Angabe" + Zoom-Cut-Hinweis (nur DTV)

// Legenden-Skala + Titel für den aktiven Modus (neu) aufbauen.
function renderLegend(m) {
  const scale = m === "sv" ? SCALE_SV : SCALE;
  const labels = m === "sv" ? SV_LABELS : DTV_LABELS;
  legendTitle.innerHTML =
    m === "sv" ? "SV-Anteil · Schwerverkehr %" : "DTV / DTV<sub>w</sub> · Kfz/24h";
  legend.innerHTML = "";
  legendRows = [];
  scale.forEach(([value, color], i) => {
    const row = document.createElement("div");
    row.className = "legend-row";
    row.innerHTML =
      `<span class="legend-swatch" style="background:${color}"></span>` +
      `<span class="legend-label">${labels[i]}</span>`;
    legend.appendChild(row);
    legendRows.push({ el: row, value });
  });
  ndRow = document.createElement("div");
  ndRow.className = "legend-row";
  ndRow.innerHTML =
    `<span class="legend-swatch" style="background:${NODATA}"></span>` +
    `<span class="legend-label">keine Angabe</span>`;
  legend.appendChild(ndRow);
  // Dynamischer Hinweis auf den Zoom-Filter (DTV-Leiter, s. tiles.yaml).
  cut = document.createElement("div");
  cut.id = "legend-cut";
  legend.appendChild(cut);
}

// Schwelle je (Ganzzahl-)Zoom – muss zur DTV-Leiter in tiles.yaml passen.
function zoomThreshold(z) {
  const fz = Math.floor(z);
  if (fz >= 8) return 0;
  if (fz === 7) return 1000;
  if (fz === 6) return 2000;
  return 10000;
}

// Ausgefilterte Bereiche in der Legende ausgrauen + Schwelle anzeigen (nur DTV-Modus;
// die Zoom-Leiter filtert nach DTV, nicht nach SV-Anteil).
function updateLegendForZoom() {
  if (mode !== "dtv") {
    for (const { el } of legendRows) el.classList.remove("dimmed");
    ndRow.classList.remove("dimmed");
    cut.style.display = "none";
    return;
  }
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

// Modus umschalten: Farb-Expression auf allen Datenebenen + Legende tauschen.
const DATA_LAYERS = [
  ["svz-lines", "line-color"],
  ["svz-points", "circle-color"],
  ["bast-points", "circle-color"],
];
const modeButtons = [...document.querySelectorAll("#legend-modes button")];
function setMode(m) {
  mode = m;
  const expr = m === "sv" ? svColorExpr : colorExpr;
  for (const [id, prop] of DATA_LAYERS) {
    if (map.getLayer(id)) map.setPaintProperty(id, prop, expr);
  }
  // UBA-HVS kennt keinen SV -> im SV-Modus grau, sonst DTV≈-Färbung.
  if (map.getLayer("hvs-lines")) {
    map.setPaintProperty("hvs-lines", "line-color", m === "sv" ? NODATA : hvsColorExpr);
  }
  for (const b of modeButtons) b.classList.toggle("active", b.dataset.mode === m);
  renderLegend(m);
  updateLegendForZoom();
}
for (const b of modeButtons) b.addEventListener("click", () => setMode(b.dataset.mode));

renderLegend("dtv");
map.on("zoom", updateLegendForZoom);
updateLegendForZoom();
