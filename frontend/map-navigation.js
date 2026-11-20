let navigateToBuilding = null;

// A map provider registers how to select a building by its campus code.
export function registerBuildingNavigator(navigate) {
  navigateToBuilding = navigate;
}

export async function showBuildingOnMap(buildingCode) {
  if (!navigateToBuilding) {
    throw new Error("The map is not available yet. Wait for it to load, or refresh to try again.");
  }
  return navigateToBuilding(buildingCode);
}
