export function createSavedPlace(input) {
  if (!input || typeof input.buildingCode !== "string" || !input.buildingCode.trim()) {
    throw new Error("Choose a building to save.");
  }
  if (typeof input.name !== "string" || !input.name.trim()) {
    throw new Error("The saved building needs a name.");
  }
  const buildingCode = input.buildingCode.trim();
  const name = input.name.trim();
  if (buildingCode.length > 20 || name.length > 200) {
    throw new Error("The building code or name is too long.");
  }
  return { buildingCode, name };
}

export function addSavedPlace(places, input) {
  const place = createSavedPlace(input);
  if (places.some(item => item.buildingCode === place.buildingCode)) return places;
  return [...places, place];
}

export function removeSavedPlace(places, buildingCode) {
  return places.filter(place => place.buildingCode !== buildingCode);
}
