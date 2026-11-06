import { useCallback, useRef, useState } from "react";

import { submitConversationTurn } from "../api/conversationTurn";
import { playAudioBlob } from "../utils/audioPlayback";

const INITIAL_STATE = {
  status: "idle",
  errorMessage: null,
  result: null,
  speechBlob: null,
  conversation: [],
};

function getReadyStatus(result) {
  if (result.conversation_ended) {
    return "conversation_ended";
  }

  const { turn } = result;
  if (turn.intent === "CONFIRMATION") {
    return "complete";
  }
  if (turn.intent === "REJECTION") {
    return "declined";
  }
  if (
    (turn.intent === "NEW_REQUEST" || turn.intent === "MODIFICATION") &&
    turn.tasks.length > 0
  ) {
    return "awaiting_confirmation";
  }
  return "awaiting_clarification";
}

export function useConversationTurn({
  roomId,
  guestLanguage,
  onResponseFinished,
}) {
  const [state, setState] = useState(INITIAL_STATE);
  const submittingRef = useRef(false);
  const conversationIdRef = useRef(null);
  const speechBlobRef = useRef(null);

  const submitRecording = useCallback(
    async (audioBlob) => {
      if (submittingRef.current) {
        return;
      }

      submittingRef.current = true;
      speechBlobRef.current = null;
      setState((current) => ({
        ...current,
        status: "uploading",
        errorMessage: null,
        speechBlob: null,
      }));

      try {
        const result = await submitConversationTurn(audioBlob, {
          roomId,
          guestLanguage,
          conversationId: conversationIdRef.current,
        });
        conversationIdRef.current = result.conversation_ended
          ? null
          : result.conversation_id;
        speechBlobRef.current = result.speechBlob;
        const readyStatus = getReadyStatus(result);

        setState((current) => ({
          ...current,
          status: "speaking",
          errorMessage: null,
          result,
          speechBlob: result.speechBlob,
          conversation: [
            ...current.conversation,
            { role: "user", text: result.raw_input.transcript },
            { role: "assistant", text: result.turn.assistant_response.text },
          ],
        }));

        try {
          await playAudioBlob(result.speechBlob);
        } catch (error) {
          setState((current) => ({
            ...current,
            status: readyStatus,
            errorMessage:
              error instanceof Error
                ? `Speech playback failed: ${error.message}`
                : "Speech playback failed.",
          }));
          return;
        }

        setState((current) => ({ ...current, status: readyStatus }));
        if (!result.conversation_ended) {
          await onResponseFinished?.();
        }
      } catch (error) {
        setState((current) => ({
          ...current,
          status: "error",
          errorMessage:
            error instanceof Error
              ? error.message
              : "Conversation processing failed.",
        }));
      } finally {
        submittingRef.current = false;
      }
    },
    [guestLanguage, onResponseFinished, roomId],
  );

  const playResponse = useCallback(async () => {
    const speechBlob = speechBlobRef.current;
    if (!speechBlob) {
      return;
    }

    try {
      await playAudioBlob(speechBlob);
      setState((current) => ({ ...current, errorMessage: null }));
    } catch (error) {
      setState((current) => ({
        ...current,
        errorMessage:
          error instanceof Error
            ? `Speech playback failed: ${error.message}`
            : "Speech playback failed.",
      }));
    }
  }, []);

  return {
    ...state,
    submitRecording,
    playResponse,
  };
}
