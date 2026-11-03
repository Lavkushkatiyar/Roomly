
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "") ?? "";

export async function synthesizeSpeech(assistantResponse) {
  if (
    !assistantResponse ||
    typeof assistantResponse.text !== "string" ||
    !assistantResponse.text.trim() ||
    typeof assistantResponse.language !== "string"
  ) {
    throw new TypeError("Invalid assistant response.");
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}/voice_generate/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(assistantResponse),
    });
  } catch {
    throw new Error("Could not reach Roomly speech service.");
  }

  if (!response.ok) {
    throw new Error(`Speech generation failed (${response.status}).`);
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.startsWith("audio/")) {
    throw new Error("Roomly returned an unexpected audio response.");
  }

  const audioBlob = await response.blob();

  if (audioBlob.size === 0) {
    throw new Error("Roomly returned empty audio.");
  }

  return audioBlob;
}
