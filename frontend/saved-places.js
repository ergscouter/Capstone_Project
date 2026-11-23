import { addSavedPlace, createSavedPlace, removeSavedPlace } from "./saved-places-model.js";
import { loadSavedPlaces, saveSavedPlaces, SAVED_PLACES_STORAGE_KEY } from "./saved-places-storage.js";
import { showBuildingOnMap } from "./map-navigation.js";

let places = [];
let selectedPlace = null;
let saveButton = null;
let buildingLoadState = "loading";
const buildingsByCode = new Map();
const placeList = document.getElementById("saved-places-list");
const emptyMessage = document.getElementById("saved-places-empty");
const feedback = document.getElementById("saved-places-feedback");
const storageStatus = document.getElementById("saved-places-storage-status");

function showFeedback(message, isError = false) {
  feedback.textContent = message;
  feedback.classList.toggle("error", isError);
}

function restoreSavedPlaces() {
  try {
    places = loadSavedPlaces().places;
    storageStatus.textContent = "Saved places stay in this browser on this device.";
    storageStatus.classList.remove("error");
  } catch {
    storageStatus.textContent = "Saved places could not be opened. Existing data has been kept. "
      + "Check that browser storage is allowed, then refresh to try again.";
    storageStatus.classList.add("error");
  }
  renderSavedPlaces();
  updateSaveButton();
}

function changePlaces(change, message) {
  try {
    // Read again before changing the list so another tab's bookmarks are kept.
    const saved = loadSavedPlaces();
    places = saved.places;
    const updated = change(places);
    saveSavedPlaces(updated, saved.snapshot);
    places = updated;
    storageStatus.textContent = "Saved places stay in this browser on this device.";
    storageStatus.classList.remove("error");
    showFeedback(message);
  } catch {
    showFeedback("Your change could not be saved. Existing saved data has been kept. "
      + "Check that browser storage is allowed and has space, or try again if another tab changed the list.", true);
  }
  renderSavedPlaces();
  updateSaveButton();
}

function updateSaveButton() {
  if (!saveButton || !selectedPlace) return;
  const saved = places.some(place => place.buildingCode === selectedPlace.buildingCode);
  saveButton.textContent = saved ? "Remove saved place" : "Save place";
  saveButton.setAttribute("aria-label", saved
    ? `Remove ${selectedPlace.name} from Saved Places`
    : `Save ${selectedPlace.name} to Saved Places`);
}

function removePlace(place) {
  changePlaces(current => removeSavedPlace(current, place.buildingCode),
    `Removed ${place.name} from Saved Places.`);
}

function renderSavedPlaces() {
  placeList.replaceChildren();
  emptyMessage.hidden = places.length > 0;
  const displayName = place => buildingsByCode.get(place.buildingCode)?.name ?? place.name;
  for (const place of [...places].sort((first, second) => displayName(first).localeCompare(displayName(second)))) {
    const item = document.createElement("li");
    const content = document.createElement("div");
    content.className = "saved-place-content";
    const building = buildingsByCode.get(place.buildingCode);
    const name = document.createElement("button");
    name.type = "button";
    name.className = "saved-place-link";
    name.textContent = displayName(place);
    name.setAttribute("aria-label", `Show ${name.textContent} on the map from Saved Places`);
    const notice = document.createElement("p");
    notice.className = "saved-places-note";
    notice.setAttribute("role", "status");
    const hasLocation = Number.isFinite(building?.lat) && Number.isFinite(building?.lon);
    name.disabled = !hasLocation;
    notice.hidden = hasLocation;
    if (!hasLocation) {
      if (buildingLoadState === "loading") notice.textContent = "Loading building location...";
      else if (buildingLoadState === "failed") notice.textContent = "Building locations are unavailable. Refresh to try again.";
      else notice.textContent = building
        ? "A map location is not available for this building."
        : "This building is no longer in the campus building list.";
    }
    name.addEventListener("click", async () => {
      name.disabled = true;
      notice.hidden = false;
      notice.classList.remove("error");
      notice.textContent = "Opening building on the map...";
      try {
        const buildingName = await showBuildingOnMap(place.buildingCode);
        notice.textContent = `Showing ${buildingName} on the map.`;
      } catch (error) {
        notice.textContent = error.message;
        notice.classList.add("error");
      } finally {
        name.disabled = false;
      }
    });
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "Remove";
    removeButton.setAttribute("aria-label", `Remove ${name.textContent} from Saved Places`);
    removeButton.addEventListener("click", () => removePlace({ ...place, name: name.textContent }));
    content.append(name, notice);
    item.append(content, removeButton);
    placeList.append(item);
  }
}

// Building details can offer bookmarks without depending on the map provider.
export function createSavePlaceButton(building) {
  const place = createSavedPlace({ buildingCode: building.code, name: building.name });
  selectedPlace = place;
  saveButton = document.createElement("button");
  saveButton.type = "button";
  saveButton.className = "save-place-button";
  saveButton.addEventListener("click", () => {
    if (places.some(item => item.buildingCode === place.buildingCode)) {
      removePlace(place);
    } else {
      changePlaces(current => addSavedPlace(current, place),
        `Added ${place.name} to Saved Places.`);
    }
  });
  updateSaveButton();
  return saveButton;
}

async function loadBuildings() {
  const response = await fetch("/api/buildings");
  if (!response.ok) throw new Error("Building locations are unavailable.");
  const buildings = await response.json();
  if (!Array.isArray(buildings)) throw new Error("Invalid building list.");
  for (const building of buildings) buildingsByCode.set(building.code, building);
  buildingLoadState = "ready";
  renderSavedPlaces();
}

window.addEventListener("storage", event => {
  if (event.storageArea === localStorage
      && (event.key === SAVED_PLACES_STORAGE_KEY || event.key === null)) {
    restoreSavedPlaces();
  }
});

restoreSavedPlaces();
loadBuildings().catch(() => {
  buildingLoadState = "failed";
  renderSavedPlaces();
});
