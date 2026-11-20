import { addSavedPlace, createSavedPlace, removeSavedPlace } from "./saved-places-model.js";

let places = [];
let selectedPlace = null;
let saveButton = null;
const placeList = document.getElementById("saved-places-list");
const emptyMessage = document.getElementById("saved-places-empty");
const feedback = document.getElementById("saved-places-feedback");

function updateSaveButton() {
  if (!saveButton || !selectedPlace) return;
  const saved = places.some(place => place.buildingCode === selectedPlace.buildingCode);
  saveButton.textContent = saved ? "Remove saved place" : "Save place";
  saveButton.setAttribute("aria-label", saved
    ? `Remove ${selectedPlace.name} from Saved Places`
    : `Save ${selectedPlace.name} to Saved Places`);
}

function removePlace(place) {
  places = removeSavedPlace(places, place.buildingCode);
  renderSavedPlaces();
  updateSaveButton();
  feedback.textContent = `Removed ${place.name} from Saved Places.`;
}

function renderSavedPlaces() {
  placeList.replaceChildren();
  emptyMessage.hidden = places.length > 0;
  for (const place of [...places].sort((first, second) => first.name.localeCompare(second.name))) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = place.name;
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "Remove";
    removeButton.setAttribute("aria-label", `Remove ${place.name} from Saved Places`);
    removeButton.addEventListener("click", () => removePlace(place));
    item.append(name, removeButton);
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
      places = addSavedPlace(places, place);
      renderSavedPlaces();
      updateSaveButton();
      feedback.textContent = `Added ${place.name} to Saved Places.`;
    }
  });
  updateSaveButton();
  return saveButton;
}

renderSavedPlaces();
