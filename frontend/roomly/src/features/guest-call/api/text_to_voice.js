import apiClient from "./client";

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
    response = await apiClient.post("voice_generate/", assistantResponse, {
      responseType: "blob",
    });
  } catch (error) {
    if (error?.response) {
      throw new Error(`Speech generation failed (${error.response.status}).`);
    }

    throw new Error("Could not reach Roomly speech service.");
  }

  const audioBlob = response.data;

  if (!(audioBlob instanceof Blob) || !audioBlob.type.startsWith("audio/")) {
    throw new Error("Roomly returned an unexpected audio response.");
  }

  if (audioBlob.size === 0) {
    throw new Error("Roomly returned empty audio.");
  }

  return audioBlob;
}
