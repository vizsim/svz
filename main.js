// Verkehrsmengenkarte – MapLibre-Viewer.
// Basemap: gehostetes OpenFreeMap-Positron. Daten in DREI PMTiles, eines je Ebene:
//   land    = Länder        (svz_de.pmtiles:       Layer `svz` Linien + `svz_points` Punkte)
//   kommune = Kommunen      (svz_kommunal.pmtiles: Layer `kommunal` Linien + `kommunal_points`)
//   bund    = BASt-Backbone (svz_bast.pmtiles:     Layer `bast`, Bundesfernstraßen A+B)
// WELCHE Quellen es gibt (Name, Ebene, Land, Jahr, Lizenz, Zugang, BBox zum Hinzoomen),
// kommt aus pipeline/data/manifest.json (`svz manifest`, gespeist aus sources.yaml) —
// hier wird KEINE Quellenliste mehr gepflegt. Einzige Ausnahme: die extern gehostete
// UBA-HVS (kein Pipeline-Produkt) steht fest im Code.
// Alle Daten-Layer hängen UNTER der ersten Symbol-(Label-)Ebene -> Labels oben.
const DATA_DIR = "pipeline/data/";
const MANIFEST_URL = DATA_DIR + "manifest.json";
// UBA-Hauptverkehrsstraßen (END 2021, bundesweit) – gehostet aus unfallkarte, als
// Fallback/Backbone. Attribut annualTrafficFlow (Kfz/Jahr), Layer `lines`.
const HVS_PMTILES_URL =
  "https://tiles.vizsim.de/file/unfallkarte-data-v2/uba/hvs_verkehrsmengen.pmtiles";

// Ebenen: Reihenfolge im Panel, PMTiles-Datensatz (manifest-Key) und Layer
// [id, typ, source-layer] — die source-layer-Namen sind der Vertrag mit tiles.yaml.
// `minZoom` = Mindest-Zoom der Kacheln (tiles.yaml) -> Hinweis im Gruppen-Kopf.
// Wording: „SVZ" (amtliche Straßenverkehrszählung) nur für Länder + Bund; die Städte
// zählen selbst -> „kommunale Zählungen", bewusst abgesetzt.
const LEVELS = {
  land: {
    label: "Länder (SVZ)",
    dataset: "svz_de",
    layers: [["svz-lines", "line", "svz"], ["svz-points", "circle", "svz_points"]],
  },
  kommune: {
    label: "Kommunen (eigene Zählungen)",
    dataset: "svz_kommunal",
    layers: [["kommunal-lines", "line", "kommunal"], ["kommunal-points", "circle", "kommunal_points"]],
    minZoom: 8,
  },
  bund: {
    label: "Bund (BASt)",
    dataset: "svz_bast",
    layers: [["bast-points", "circle", "bast"]],
  },
};
const LEVEL_ORDER = ["land", "kommune", "bund"];
const ALL_LAYERS = LEVEL_ORDER.flatMap((l) => LEVELS[l].layers);

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

// --- Quellen aus dem Manifest (status: live) + fest verdrahtete UBA-HVS ---------------
const manifest = await fetch(MANIFEST_URL).then((r) => r.json()).catch(() => ({}));
const SOURCES = Object.entries(manifest._sources || {})
  .filter(([, s]) => s.status === "live" && LEVELS[s.level])
  .map(([code, s]) => ({
    code, name: s.name, level: s.level, state: s.state, year: s.year, metric: s.metric,
    license: s.license, bbox: s.bbox, n: s.n,
    access: (s.access || []).map((a) => ({ l: a.label, u: a.url })),
  }));
SOURCES.push({
  code: "hvs", name: "UBA-Hauptverkehrsstraßen", level: "bund", year: 2021, metric: "DTV≈",
  license: "© UBA", layer: "hvs-lines", default: false, minZoom: 9, hint: "nur Straßen > 3 Mio Kfz/Jahr",
  access: [{ l: "Viewer", u: "https://gis.uba.de/maps/resources/apps/laermkartierung/index.html?lang=de" }],
});
// Länder/Kommunen alphabetisch; Bund in Manifest-Reihenfolge (BASt vor HVS).
const collator = new Intl.Collator("de");
const GROUPS = LEVEL_ORDER.map((level) => {
  const items = SOURCES.filter((s) => s.level === level);
  if (level !== "bund") items.sort((a, b) => collator.compare(a.name, b.name));
  return { level, sources: items };
});
const SRC = Object.fromEntries(SOURCES.map((s) => [s.code, s]));

// pmtiles-Protokoll registrieren.
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

// Fehlt der Wert (keine Zählung), NICHT als 0 einfärben, sondern grau.
const NODATA = "#b4b4b4";

// SV-Anteil je Feature: direkt sv_anteil (%), sonst aus dtv_sv/dtv_kfz berechnet.
const svShare = [
  "case",
  ["has", "sv_anteil"], ["to-number", ["get", "sv_anteil"]],
  ["*", ["/", ["to-number", ["get", "dtv_sv"]], ["to-number", ["get", "dtv_kfz"]]], 100],
];
// grau, wenn weder Anteil noch (SV & DTV>0) vorliegt.
const hasSv = [
  "any",
  ["has", "sv_anteil"],
  ["all", ["has", "dtv_sv"], ["has", "dtv_kfz"], [">", ["to-number", ["get", "dtv_kfz"]], 0]],
];

// Wertebereich der zweiten Färbung (SV-Anteil %). SCALE (DTV, oben) und SCALE_SV =
// [Schwelle, Standardfarbe]; die Schwellen gelten für beide Paletten.
const SCALE_SV = [
  [0, "#1a9850"],
  [5, "#66bd63"],
  [10, "#d9ef8b"],
  [15, "#fee08b"],
  [20, "#fdae61"],
  [25, "#f46d43"],
  [30, "#d73027"],
];
// Barrierefreie Alternativrampe: RdYlBu (Blau=niedrig -> hell -> Rot=hoch). Ersetzt nur
// das CVD-kritische Grün des Standard-Verlaufs durch Blau -> bleibt mehrfarbig UND bei
// Rot-Grün-Schwäche unterscheidbar (worst Klassenpaar deutan ΔE 16.1 statt 1.3 bei Grün-Rot).
const CB_STOPS = ["#4575b4", "#91bfdb", "#e0f3f8", "#ffffbf", "#fee090", "#fc8d59", "#d73027"];

// interpolate-Färbung aus Wert + Schwellen/Farben; `stops` überschreibt die Farben (CB).
function rampColor(valueExpr, hasExpr, scale, stops) {
  const interp = ["interpolate", ["linear"], valueExpr];
  scale.forEach(([v, c], i) => interp.push(v, stops ? stops[i] : c));
  return ["case", hasExpr, interp, NODATA];
}
// Farb-Expression je Modus ("dtv"|"sv") und Palette (cb = barrierefrei).
const colorExprFor = (m, cb) =>
  m === "sv"
    ? rampColor(svShare, hasSv, SCALE_SV, cb ? CB_STOPS : null)
    : rampColor(["get", "dtv_kfz"], ["has", "dtv_kfz"], SCALE, cb ? CB_STOPS : null);
// UBA-HVS: annualTrafficFlow (Kfz/Jahr) -> DTV-Äquivalent (÷365), gleiche DTV-Skala.
const hvsColorExprFor = (cb) =>
  rampColor(["/", ["to-number", ["get", "annualTrafficFlow"]], 365],
    ["has", "annualTrafficFlow"], SCALE, cb ? CB_STOPS : null);

// Initiale Färbung (DTV, Standardpalette) für die addLayer-Aufrufe.
const colorExpr = colorExprFor("dtv", false);
const hvsColorExpr = hvsColorExprFor(false);

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

// --- Titelzeile: SVZ (Länder + BASt) klar getrennt von den kommunalen Zählungen -------
const nLand = GROUPS.find((g) => g.level === "land").sources.length;
const nKomm = GROUPS.find((g) => g.level === "kommune").sources.length;
document.getElementById("state-line").textContent =
  `SVZ: ${nLand} Länder + BASt · dazu kommunale Zählungen: ${nKomm} Städte`;

// --- Quellen-Panel: je Ebene eine Gruppe (Kopf mit Gruppen-Checkbox + Auf-/Zuklappen),
//     darunter die Quellen (Name · Jahr · Lizenz · Zugang, ⌖ = hinzoomen) ---------------
const srcAll = document.getElementById("src-all");
const srcTable = document.getElementById("sources-table");

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

// Auf die BBox einer Quelle zoomen (Manifest: [W,S,E,N]); Kommunen sind klein -> maxZoom.
const zoomTo = (s) =>
  map.fitBounds([[s.bbox[0], s.bbox[1]], [s.bbox[2], s.bbox[3]]],
    { padding: 60, maxZoom: s.level === "kommune" ? 13 : 9, duration: 900 });
// Fadenkreuz-Icon als Inline-SVG (Unicode ⌖ fehlt in vielen Systemschriften -> Tofu).
const ZOOM_ICON =
  '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">' +
  '<circle cx="8" cy="8" r="4"/><path d="M8 1v3M8 12v3M1 8h3M12 8h3"/></svg>';

for (const g of GROUPS) {
  const lvl = LEVELS[g.level];
  const tbody = document.createElement("tbody");
  tbody.className = "src-group";
  tbody.dataset.level = g.level;

  // Gruppen-Kopf: Checkbox (alle der Ebene), Klapp-Pfeil, Label, Anzahl, Zoom-Hinweis.
  const head = document.createElement("tr");
  head.className = "src-group-head";
  head.innerHTML =
    `<td><input type="checkbox" checked></td>` +
    `<td colspan="4"><button type="button" class="src-group-toggle" aria-expanded="true">▾</button>` +
    `${lvl.label} <span class="src-count">${g.sources.length}</span>` +
    `<span class="src-group-hint"></span></td>`;
  g.cb = head.querySelector("input");
  g.hintEl = head.querySelector(".src-group-hint");
  const toggle = head.querySelector(".src-group-toggle");
  const setOpen = (open) => {
    tbody.classList.toggle("collapsed", !open);
    toggle.textContent = open ? "▾" : "▸";
    toggle.setAttribute("aria-expanded", String(open));
  };
  toggle.addEventListener("click", () => setOpen(tbody.classList.contains("collapsed")));
  g.cb.addEventListener("change", () => {
    for (const s of g.sources) s.el.checked = g.cb.checked;
    applySources();
  });
  tbody.append(head);

  for (const s of g.sources) {
    const tr = document.createElement("tr");
    tr.className = "src-row";
    const state = s.level === "kommune" ? `<span class="src-state">${s.state}</span>` : "";
    const zoom = s.bbox ? `<button type="button" class="src-zoom" title="hinzoomen">${ZOOM_ICON}</button>` : "";
    tr.innerHTML =
      `<td><input type="checkbox" checked></td>` +
      `<td class="src-name">${s.name}${state}${zoom}</td>` +
      `<td class="src-year">${s.year}</td>` +
      `<td class="src-lic">${licenseCell(s.license)}</td>` +
      `<td class="src-access">${accessCell(s.access)}</td>`;
    const cb = tr.querySelector("input");
    cb.checked = s.default !== false; // HVS startet ausgeblendet (default:false)
    s.el = cb;
    cb.addEventListener("change", applySources);
    tr.querySelector(".src-zoom")?.addEventListener("click", (e) => { e.stopPropagation(); zoomTo(s); });
    tr.addEventListener("click", (e) => {
      if (e.target.closest("a, button") || e.target === cb) return; // Links/Buttons nicht abfangen
      cb.checked = !cb.checked;
      applySources();
    });
    tbody.append(tr);
    if (s.hint) {
      const ht = document.createElement("tr");
      ht.className = "src-hint";
      ht.innerHTML = `<td colspan="5"></td>`;
      tbody.append(ht);
      s.hintEl = ht;
    }
  }
  srcTable.append(tbody);
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

// Panel-Höhe: so hoch wie nötig, aber nie über die Legende — max-height = Abstand
// Panel-Oberkante -> Legenden-Oberkante (minus Luft); die Quellenliste scrollt intern.
// Reagiert auf Fenstergröße und auf Höhenänderungen der Legende (DTV/SV-Umschaltung).
const titleEl = document.getElementById("title");
const legendEl = document.getElementById("legend");
function fitPanel() {
  const top = titleEl.getBoundingClientRect().top;
  const legendTop = legendEl.getBoundingClientRect().top;
  titleEl.style.maxHeight = `${Math.max(140, legendTop - top - 10)}px`;
}
window.addEventListener("resize", fitPanel);
new ResizeObserver(fitPanel).observe(legendEl);
fitPanel();

// Alle Pipeline-Layer filtern nach `source` (Schlüssel aus sources.yaml) — egal ob Land,
// Kommune oder BASt; nur die extern gehostete HVS schaltet ihren Layer per Visibility.
function applySources() {
  const on = SOURCES.filter((s) => s.el.checked && !s.layer).map((s) => s.code);
  const filt = ["in", ["get", "source"], ["literal", on]];
  for (const id of [...ALL_LAYERS.map(([id]) => id), "kommune-marker", "kommune-marker-label"]) {
    if (map.getLayer(id)) map.setFilter(id, filt);
  }
  for (const s of SOURCES) {
    if (s.layer && map.getLayer(s.layer)) {
      map.setLayoutProperty(s.layer, "visibility", s.el.checked ? "visible" : "none");
    }
  }
  // Gruppen-Checkboxen (an / aus / teilweise) + „alle Quellen".
  for (const g of GROUPS) {
    const all = g.sources.every((s) => s.el.checked);
    g.cb.checked = all;
    g.cb.indeterminate = !all && g.sources.some((s) => s.el.checked);
  }
  const all = SOURCES.every((s) => s.el.checked);
  srcAll.checked = all;
  srcAll.indeterminate = !all && SOURCES.some((s) => s.el.checked);
  updateZoomHints(); // Hinweiszeilen an den (Un)Check-Zustand anpassen
}

// Hinweise: im Gruppen-Kopf „erst ab Zoom N" (Ebene mit minZoom, z.B. Kommunen ab 8),
// unter einer Quelle dauerhaft `hint` + ggf. „erst ab Zoom N"-Vorsatz (UBA-HVS).
function updateZoomHints() {
  const z = map.getZoom();
  for (const g of GROUPS) {
    const lvl = LEVELS[g.level];
    const below = lvl.minZoom && z < lvl.minZoom && g.sources.some((s) => s.el.checked);
    g.hintEl.textContent = below ? `erst ab Zoom ${lvl.minZoom} · Fadenkreuz zoomt hin` : "";
  }
  for (const s of SOURCES) {
    if (!s.hintEl) continue;
    if (!s.el.checked) {
      s.hintEl.style.display = "none"; // Hinweis nur bei aktivierter Quelle
      continue;
    }
    s.hintEl.style.display = "";
    const prefix = s.minZoom && z < s.minZoom ? `erst ab Zoom ${s.minZoom} · ` : "";
    s.hintEl.querySelector("td").textContent = prefix + (s.hint || "");
  }
}
map.on("zoom", updateZoomHints);
updateZoomHints();

// Layer-Definitionen (Linien/Kreise) — gleiche Optik für alle Ebenen; Unterscheidung
// läuft über das Panel (Ebene/Quelle) und das Popup (Herausgeber).
const lineLayer = (id, source, sourceLayer, extraLayout = {}) => ({
  id, type: "line", source, "source-layer": sourceLayer,
  layout: { "line-cap": "round", "line-join": "round", ...extraLayout },
  paint: {
    "line-color": colorExpr,
    "line-opacity": 0.9,
    "line-width": ["interpolate", ["linear"], ["zoom"], 6, 1.0, 9, 1.8, 13, 3.5, 16, 7],
  },
});
const circleLayer = (id, source, sourceLayer) => ({
  id, type: "circle", source, "source-layer": sourceLayer,
  paint: {
    "circle-color": colorExpr,
    "circle-opacity": 0.9,
    "circle-stroke-color": "#ffffff",
    "circle-stroke-width": 0.7,
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, 2, 10, 4, 14, 7],
  },
});

map.on("load", () => {
  // Beide Daten-Layer direkt unter die erste Symbol-(Label-)Ebene legen.
  const firstSymbol = map.getStyle().layers.find((l) => l.type === "symbol")?.id;

  // Je Ebene eine PMTiles-Quelle (aus dem Manifest: Datei + Attribution). Reihenfolge =
  // Zeichenreihenfolge: Länder unten, Kommunen darüber (lokal detaillierter), BASt oben.
  const ATTRIB = {
    land: 'Verkehrsmengen: <a href="https://github.com/vizsim/svz#datenquellen-der-16-bundesl%C3%A4nder" target="_blank" rel="noopener">Straßenbauverwaltungen der Länder</a>',
    kommune: 'Kommunale Zählungen: <a href="https://github.com/vizsim/svz#kommunale-verkehrsz%C3%A4hlungen-keine-svz" target="_blank" rel="noopener">Städte (s. Quellen)</a>',
    bund: 'Bundesfernstraßen: © <a href="https://www.bast.de/DE/Publikationen/Statistik/Verkehrsdaten/Manuelle-Zaehlung.html" target="_blank" rel="noopener">BASt</a>',
  };
  for (const level of ["land", "kommune", "bund"]) {
    const lvl = LEVELS[level];
    const ds = manifest[lvl.dataset];
    if (ds && ds.present === false) continue; // Datensatz (noch) nicht gebaut
    const file = ds?.file || `svz/${lvl.dataset}.pmtiles`;
    map.addSource(level, { type: "vector", url: "pmtiles://" + DATA_DIR + file, attribution: ATTRIB[level] });
    for (const [id, type, sourceLayer] of lvl.layers) {
      map.addLayer(type === "line" ? lineLayer(id, level, sourceLayer) : circleLayer(id, level, sourceLayer), firstSymbol);
    }
  }

  // UBA-Hauptverkehrsstraßen (bundesweit, END 2021) als Fallback/Backbone — eigene,
  // gehostete Quelle, initial aus. Unter die Länder-Linien gelegt (Länderdaten oben).
  map.addSource("hvs", {
    type: "vector",
    url: "pmtiles://" + HVS_PMTILES_URL,
    attribution:
      'Hauptverkehrsstraßen: © <a href="https://gis.uba.de/maps/resources/apps/laermkartierung/index.html?lang=de" target="_blank" rel="noopener">UBA</a>',
  });
  const hvs = lineLayer("hvs-lines", "hvs", "lines", { visibility: "none" });
  hvs.paint["line-color"] = hvsColorExpr;
  map.addLayer(hvs, map.getLayer("svz-lines") ? "svz-lines" : firstSymbol);

  // Übersichts-Marker „hier gibt es kommunale Daten": unterhalb des Kommunen-Mindestzooms
  // je Stadt ein beschrifteter Punkt (BBox-Mitte aus dem Manifest), Klick zoomt hin.
  // Über den Labels, damit die Städte auf Deutschland-Zoom auffindbar bleiben.
  const kommunen = GROUPS.find((g) => g.level === "kommune").sources.filter((s) => s.bbox);
  // Schrift aus dem Basemap-Style übernehmen (Glyph-Server des Styles), möglichst nicht kursiv.
  const fonts = map.getStyle().layers.flatMap((l) =>
    l.type === "symbol" && Array.isArray(l.layout?.["text-font"]) ? [l.layout["text-font"]] : []);
  const font = fonts.find((f) => /Bold/.test(f[0])) || fonts.find((f) => /Regular/.test(f[0])) || fonts[0] || ["Noto Sans Regular"];
  map.addSource("kommune-marker", {
    type: "geojson",
    data: {
      type: "FeatureCollection",
      features: kommunen.map((s) => ({
        type: "Feature",
        properties: { source: s.code, name: s.name },
        geometry: { type: "Point", coordinates: [(s.bbox[0] + s.bbox[2]) / 2, (s.bbox[1] + s.bbox[3]) / 2] },
      })),
    },
  });
  // Auffällig gegenüber den Länder-Punkten: größerer weißer Kreis mit blauem Ring, Label
  // darf Basemap-Labels überdecken (es sind nur wenige Städte).
  map.addLayer({
    id: "kommune-marker", type: "circle", source: "kommune-marker", maxzoom: LEVELS.kommune.minZoom,
    paint: { "circle-radius": 7, "circle-color": "#ffffff", "circle-stroke-color": "#4576c4", "circle-stroke-width": 2.5 },
  });
  map.addLayer({
    id: "kommune-marker-label", type: "symbol", source: "kommune-marker", maxzoom: LEVELS.kommune.minZoom,
    layout: {
      "text-field": ["get", "name"], "text-font": font, "text-size": 12,
      "text-offset": [0, 1.0], "text-anchor": "top", "text-allow-overlap": true, "text-ignore-placement": true,
    },
    paint: { "text-color": "#4576c4", "text-halo-color": "#ffffff", "text-halo-width": 1.8 },
  });
  map.on("click", "kommune-marker", (e) => zoomTo(SRC[e.features[0].properties.source]));
  map.on("mouseenter", "kommune-marker", () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", "kommune-marker", () => (map.getCanvas().style.cursor = ""));

  // Initiale Quellen-Sichtbarkeit setzen (Layer existieren jetzt).
  applySources();

  // Klick-Popup + Cursor für alle Daten-Layer.
  const fmt = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"));
  const pct = (num, den) =>
    den ? ((Number(num) / Number(den)) * 100).toLocaleString("de-DE", { maximumFractionDigits: 1 }) : null;

  // Straßenklasse-Kürzel -> Klartext (G = städtisches Netz / Klasse lt. Quelle offen).
  const ROAD_CLASS = { A: "Autobahn", B: "Bundesstraße", L: "Landesstraße", K: "Kreisstraße", G: "Gemeinde-/Stadtstraße" };
  // Herausgeber: Kommune „Ravensburg (BW)", Bund „BASt", Länder ihr Kürzel.
  const providerLabel = (p) => {
    const s = SRC[p.source];
    if (s?.level === "kommune") return `${s.name} (${s.state})`;
    if (s?.level === "bund" || p.state === "DE") return "BASt";
    return p.state;
  };

  // Metrik-Badge mit Erklär-Tooltip (hover) – DTV/DTVw/DTV≈/24h ausgeschrieben.
  const METRIC_TITLE = {
    DTV: "Durchschnittliche tägliche Verkehrsstärke (Kfz/24h, alle Tage)",
    DTVw: "Durchschnittliche tägliche Verkehrsstärke werktags (Mo–Fr)",
    "DTV≈": "Näherung aus Jahresmenge: Kfz/Jahr ÷ 365",
    "24h": "Einzelzählung über 24 h an einem Werktag (Di/Do) – kein Jahresmittel wie DTV",
  };
  const METRIC_LABEL = { "24h": "24h-Zählung" };
  const metricBadge = (m) =>
    `<span class="popup-metric" title="${METRIC_TITLE[m] || ""}">${METRIC_LABEL[m] || m}</span>`;

  // „SV" = Schwerverkehr; Label mit Erklär-Tooltip beim Hovern.
  const svLabel = (t) => `<span class="popup-hint" title="Schwerverkehr: Lkw, Lastzüge, Busse (Kfz > 3,5 t)">${t}</span>`;

  // „Hero"-Zeile: große Zahl + gedämpfte Einheit + Metrik-Badge.
  const dtvHero = (val, metric) =>
    `<div class="popup-dtv">${fmt(val)} <span class="popup-unit">Kfz/24h</span> ${metricBadge(metric)}</div>`;

  const popup = (lngLat, html) =>
    new maplibregl.Popup({ closeButton: false, maxWidth: "290px" })
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
    // Titel: Straßen-/Knotenname (kommunal), sonst Straßennummer, sonst Klasse.
    const title = p.name || p.road_no || `${p.road_class}-Straße`;
    const klass = ROAD_CLASS[p.road_class] || `Klasse ${p.road_class}`;
    const klassLine = p.name && p.road_no ? `${klass} ${p.road_no}` : klass;

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
      `<div class="popup-road">${title}</div>` +
        dtvLine +
        sv +
        `<div class="popup-meta">${klassLine} · ${p.year} · ${providerLabel(p)}</div>`,
    );
  };
  for (const id of [...ALL_LAYERS.map(([id]) => id), "hvs-lines"]) {
    if (!map.getLayer(id)) continue;
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
let cb = false;       // barrierefreie (CVD-sichere) Palette an/aus
let legendRows = [];  // pro Modus neu aufgebaut
let ndRow, cut;       // "keine Angabe" + Zoom-Cut-Hinweis (nur DTV)

// Legenden-Skala + Titel für Modus + Palette (neu) aufbauen.
function renderLegend(m, cb) {
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
      `<span class="legend-swatch" style="background:${cb ? CB_STOPS[i] : color}"></span>` +
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

// Färbung (Modus + Palette) auf allen Datenebenen anwenden + Legende neu bauen.
const DATA_LAYERS = ALL_LAYERS.map(([id, type]) => [id, type === "line" ? "line-color" : "circle-color"]);
function applyColors() {
  const expr = colorExprFor(mode, cb);
  for (const [id, prop] of DATA_LAYERS) {
    if (map.getLayer(id)) map.setPaintProperty(id, prop, expr);
  }
  // UBA-HVS kennt keinen SV -> im SV-Modus grau, sonst DTV≈-Färbung (Palette folgt cb).
  if (map.getLayer("hvs-lines")) {
    map.setPaintProperty("hvs-lines", "line-color", mode === "sv" ? NODATA : hvsColorExprFor(cb));
  }
  renderLegend(mode, cb);
  updateLegendForZoom();
}

// DTV <-> SV-Anteil (Modus-Toggle).
const modeButtons = [...document.querySelectorAll("#legend-modes button")];
function setMode(m) {
  mode = m;
  for (const b of modeButtons) b.classList.toggle("active", b.dataset.mode === m);
  applyColors();
}
for (const b of modeButtons) b.addEventListener("click", () => setMode(b.dataset.mode));

// Barrierefreie Farben (CVD-sichere Blau-Rampe) an/aus.
const cvdToggle = document.getElementById("cvd-toggle");
cvdToggle.addEventListener("change", () => { cb = cvdToggle.checked; applyColors(); });

renderLegend("dtv", false);
map.on("zoom", updateLegendForZoom);
updateLegendForZoom();
