import { createSavedPlace } from "./saved-places-model.js";

export const SAVED_PLACES_STORAGE_KEY = "eagle-eye.saved-places";
const STORAGE_VERSION = 1;

function validatePlaces(places) {
  if (!Array.isArray(places)) throw new Error("Invalid saved places list.");
  const validated = places.map(createSavedPlace);
  const codes = new Set(validated.map(place => place.buildingCode));
  if (codes.size !== validated.length) throw new Error("The saved places list contains duplicates.");
  return validated;
}

export function loadSavedPlaces() {
  const raw = localStorage.getItem(SAVED_PLACES_STORAGE_KEY);
  if (raw === null) return { places: [], snapshot: null };
  const saved = JSON.parse(raw);
  if (!saved || saved.version !== STORAGE_VERSION) {
    throw new Error("The saved places format is not supported.");
  }
  return { places: validatePlaces(saved.places), snapshot: raw };
}

export function saveSavedPlaces(places, expectedSnapshot) {
  const saved = { version: STORAGE_VERSION, places: validatePlaces(places) };
  if (localStorage.getItem(SAVED_PLACES_STORAGE_KEY) !== expectedSnapshot) {
    throw new Error("Saved Places changed in another tab. Try your change again.");
  }
  localStorage.setItem(SAVED_PLACES_STORAGE_KEY, JSON.stringify(saved));
}
