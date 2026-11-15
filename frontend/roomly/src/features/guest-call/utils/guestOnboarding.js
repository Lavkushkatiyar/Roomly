const STORAGE_KEY_PREFIX = "roomly.guest-onboarding:";

function getStorageKey(roomId) {
  if (typeof roomId !== "string" || roomId.length === 0) {
    throw new TypeError("Roomly received invalid room details for onboarding.");
  }

  return `${STORAGE_KEY_PREFIX}${roomId}`;
}

export function hasGuestSkippedOnboarding(roomId) {
  try {
    return localStorage.getItem(getStorageKey(roomId)) === "true";
  } catch (error) {
    console.warn("Could not read the saved Roomly onboarding preference.", error);
    return false;
  }
}

export function saveGuestOnboardingPreference(roomId) {
  localStorage.setItem(getStorageKey(roomId), "true");
}
