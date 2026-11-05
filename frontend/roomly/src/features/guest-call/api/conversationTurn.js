import apiClient from "./client";
import { convertAudioToWav } from "../utils/audio";

function decodeAudio(audio) {
  const binary = atob(audio.audio_base64);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return new Blob([bytes], { type: audio.content_type });
}

function isConversationTurnResponse(payload) {
  return (
    payload !== null &&
    typeof payload === "object" &&
    typeof payload.conversation_id === "string" &&
    typeof payload.conversation_ended === "boolean" &&
    payload.raw_input !== null &&
    typeof payload.raw_input?.transcript === "string" &&
    payload.turn !== null &&
    typeof payload.turn?.intent === "string" &&
    Array.isArray(payload.turn?.tasks) &&
    typeof payload.turn?.assistant_response?.text === "string" &&
    typeof payload.turn?.assistant_response?.language === "string" &&
    typeof payload.audio?.audio_base64 === "string" &&
    typeof payload.audio?.content_type === "string"
  );
}

export async function submitConversationTurn(
  audioBlob,
  { roomId, guestLanguage, conversationId },
) {
  const wavBlob = await convertAudioToWav(audioBlob);
  const formData = new FormData();
  formData.append("audio", wavBlob, "roomly-recording.wav");
  formData.append("room_id", roomId);
  formData.append("guest_language", guestLanguage);
  if (conversationId) {
    formData.append("conversation_id", conversationId);
  }

  let response;
  try {
    response = await apiClient.post("conversations/turns", formData, {
      timeout: 420_000,
    });
  } catch (error) {
    const detail = error?.response?.data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : error?.code === "ECONNABORTED" || error?.code === "ETIMEDOUT"
          ? "Roomly took too long to process this recording. Please try again."
          : "Could not process this recording. Check that Roomly is running and try again.";
    throw new Error(message, { cause: error });
  }

  if (!isConversationTurnResponse(response.data)) {
    throw new Error("Roomly returned an unexpected conversation response.");
  }

  return {
    ...response.data,
    speechBlob: decodeAudio(response.data.audio),
  };
}
