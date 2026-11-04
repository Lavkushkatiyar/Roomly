export const GUEST_LANGUAGES = [
  { label: "English", value: "en-IN" },
  { label: "Hindi", value: "hi-IN" },
  { label: "Hinglish", value: "hi-en" },
  { label: "Tamil", value: "ta-IN" },
  { label: "Telugu", value: "te-IN" },
  { label: "Kannada", value: "kn-IN" },
  { label: "Malayalam", value: "ml-IN" },
  { label: "Marathi", value: "mr-IN" },
  { label: "Bengali", value: "bn-IN" },
  { label: "Gujarati", value: "gu-IN" },
  { label: "Punjabi", value: "pa-IN" },
];

const STORAGE_KEY = "roomly.guest-session";
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isGuestSession(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    typeof value.roomId === "string" &&
    UUID_PATTERN.test(value.roomId) &&
    typeof value.roomNumber === "string" &&
    GUEST_LANGUAGES.some((language) => language.value === value.guestLanguage)
  );
}

export function loadGuestSession() {
  try {
    const storedValue = localStorage.getItem(STORAGE_KEY);
    if (!storedValue) {
      return null;
    }

    const parsedValue = JSON.parse(storedValue);
    return isGuestSession(parsedValue) ? parsedValue : null;
  } catch (error) {
    console.warn("Could not read the saved Roomly guest session.", error);
    return null;
  }
}

export function saveGuestSession(session) {
  if (!isGuestSession(session)) {
    throw new TypeError("Roomly received invalid guest session details.");
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}
