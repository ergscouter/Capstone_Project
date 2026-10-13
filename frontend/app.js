// Campus Buddy - Sprint 1 map view: shows UNT buildings, search, and building details.

const CAMPUS_CENTER = [33.2105, -97.1475];

const map = L.map("map").setView(CAMPUS_CENTER, 16);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const markers = new Map(); // building code -> Leaflet marker
const detailsPanel = document.getElementById("details");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const resultsList = document.getElementById("results");

function formatNumber(value, unit) {
  return value == null ? "Unknown" : `${value.toLocaleString()} ${unit}`;
}

function showDetails(building) {
  // textContent (not innerHTML) keeps building names from injecting markup.
  const heading = document.createElement("h2");
  heading.textContent = building.name;

  const rows = [
    ["Building code", building.code],
    ["Footprint", formatNumber(building.footprint_sqft, "sq ft")],
    ["Perimeter", formatNumber(building.perimeter_ft, "ft")],
    [
      "Location",
      building.lat == null
        ? "Unknown"
        : `${building.lat.toFixed(5)}, ${building.lon.toFixed(5)}`,
    ],
  ];

  const list = document.createElement("dl");
  for (const [label, value] of rows) {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    list.append(term, description);
  }

  detailsPanel.replaceChildren(heading, list);
}

function focusBuilding(building) {
  showDetails(building);
  const marker = markers.get(building.code);
  if (marker) {
    map.setView(marker.getLatLng(), 18);
    marker.openTooltip();
  }
}

function renderResults(matches) {
  resultsList.replaceChildren();
  if (matches.length === 0) {
    const item = document.createElement("li");
    item.textContent = "No buildings match that search.";
    resultsList.append(item);
    return;
  }
  for (const building of matches) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${building.name} (${building.code})`;
    button.addEventListener("click", () => focusBuilding(building));
    item.append(button);
    resultsList.append(item);
  }
}

async function loadBuildings() {
  const response = await fetch("/api/buildings");
  if (!response.ok) {
    throw new Error(`Could not load buildings (HTTP ${response.status}).`);
  }
  const buildings = await response.json();

  for (const building of buildings) {
    if (building.lat == null || building.lon == null) continue; // no map point
    const marker = L.circleMarker([building.lat, building.lon], {
      radius: 6,
      weight: 1,
      color: "#1f5f8b",
      fillColor: "#4a90c2",
      fillOpacity: 0.8,
    })
      .addTo(map)
      .bindTooltip(building.name);
    marker.on("click", () => showDetails(building));
    markers.set(building.code, marker);
  }
}

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = searchInput.value.trim();
  if (!query) return;
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error(`Search failed (HTTP ${response.status}).`);
    renderResults(await response.json());
  } catch (error) {
    detailsPanel.textContent = error.message;
  }
});

loadBuildings().catch((error) => {
  detailsPanel.textContent = error.message;
});
