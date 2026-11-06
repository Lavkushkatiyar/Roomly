export const GUEST_LANGUAGES = [
  { label: "English (English)", value: "en-IN" },
  { label: "Hindi (हिन्दी)", value: "hi-IN" },
  { label: "Hinglish (हिंग्लिश)", value: "hi-en" },
  { label: "Tamil (தமிழ்)", value: "ta-IN" },
  { label: "Telugu (తెలుగు)", value: "te-IN" },
  { label: "Kannada (ಕನ್ನಡ)", value: "kn-IN" },
  { label: "Malayalam (മലയാളം)", value: "ml-IN" },
  { label: "Marathi (मराठी)", value: "mr-IN" },
  { label: "Bengali (বাংলা)", value: "bn-IN" },
  { label: "Gujarati (ગુજરાતી)", value: "gu-IN" },
  { label: "Punjabi (ਪੰਜਾਬੀ)", value: "pa-IN" },
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

export function clearGuestSession() {
  localStorage.removeItem(STORAGE_KEY);
}
