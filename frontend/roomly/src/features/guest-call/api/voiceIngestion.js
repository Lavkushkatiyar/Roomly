import { convertAudioToWav } from "../utils/audio";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "") ?? "";
const ROOM_ID = import.meta.env.VITE_ROOM_ID?.trim() ?? "";
const GUEST_LANGUAGE = import.meta.env.VITE_GUEST_LANGUAGE?.trim() || "en-IN";
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isIngestionResponse(payload) {
  return (
    payload !== null &&
    typeof payload === "object" &&
    payload.raw_input !== null &&
    typeof payload.raw_input === "object" &&
    typeof payload.raw_input.transcript === "string" &&
    payload.extraction !== null &&
    typeof payload.extraction === "object" &&
    Array.isArray(payload.extraction.tasks) &&
    payload.extraction.tasks.every(
      (task) =>
        task !== null &&
        typeof task === "object" &&
        typeof task.category === "string" &&
        typeof task.staff_summary === "string" &&
        typeof task.priority === "string",
    )
  );
}

async function getErrorMessage(response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    const body = await response.text();
    let payload;

    try {
      payload = JSON.parse(body);
    } catch {
      return `Voice ingestion failed (${response.status}). Please try again.`;
    }

    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
  }

  return `Voice ingestion failed (${response.status}). Please try again.`;
}

export async function ingestVoiceRecording(audioBlob) {
  if (!UUID_PATTERN.test(ROOM_ID)) {
    throw new Error(
      "Roomly is not configured for a hotel room. Set VITE_ROOM_ID to the UUID of an existing room.",
    );
  }

  const wavBlob = await convertAudioToWav(audioBlob);
  const formData = new FormData();
  formData.append("audio", wavBlob, "roomly-recording.wav");
  formData.append("room_id", ROOM_ID);
  formData.append("guest_language", GUEST_LANGUAGE);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/voice/ingest`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error(
      "Could not reach Roomly. Check that the backend is running and try again.",
    );
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    throw new Error("Roomly returned an unexpected response. Please try again.");
  }

  const payload = await response.json();
  if (!isIngestionResponse(payload)) {
    throw new Error("Roomly returned an unexpected response. Please try again.");
  }

  return payload;
}
