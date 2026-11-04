
import { useCallback, useRef, useState } from "react";

import {
  confirmVoiceRecording,
  ingestVoiceRecording,
} from "../api/voiceIngestion";
import { createServiceRequests } from "../api/serviceRequests";
import { synthesizeSpeech } from "../api/text_to_voice";
import { playAudioBlob } from "../utils/audioPlayback";

const INITIAL_STATE = {
  status: "idle",
  errorMessage: null,
  result: null,
  confirmation: null,
  speechBlob: null,
  conversation: [],
};

export function useVoiceIngestion() {
  const [state, setState] = useState(INITIAL_STATE);
  const submittingRef = useRef(false);
  const speechBlobRef = useRef(null);

  const reset = useCallback(() => {
    speechBlobRef.current = null;
    setState(INITIAL_STATE);
  }, []);

  const speak = useCallback(async (text, language) => {
    const speechBlob = await synthesizeSpeech({ text, language });
    speechBlobRef.current = speechBlob;
    setState((current) => ({ ...current, speechBlob }));
    await playAudioBlob(speechBlob);
  }, []);

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

  const submitRecording = useCallback(
    async (audioBlob, { continueConversation = false } = {}) => {
      if (submittingRef.current) {
        return;
      }

      submittingRef.current = true;
      speechBlobRef.current = null;
      setState((current) => ({
        ...(continueConversation
          ? current
          : { ...INITIAL_STATE, conversation: [] }),
        status: "uploading",
        errorMessage: null,
        speechBlob: null,
      }));

      try {
        const result = await ingestVoiceRecording(audioBlob);
        const readyStatus =
          result.extraction.tasks.length === 0
            ? "awaiting_clarification"
            : "awaiting_confirmation";

        setState((current) => ({
          ...current,
          status: "speaking",
          errorMessage: null,
          result,
          confirmation: null,
          conversation: [
            ...current.conversation,
            { role: "user", text: result.raw_input.transcript },
            { role: "assistant", text: result.assistant_response.text },
          ],
        }));

        try {
          await speak(
            result.assistant_response.text,
            result.assistant_response.language,
          );
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
      } catch (error) {
        setState((current) => ({
          ...current,
          status: "error",
          errorMessage:
            error instanceof Error
              ? error.message
              : "Voice processing failed.",
        }));
      } finally {
        submittingRef.current = false;
      }
    },
    [speak],
  );

  const submitConfirmation = useCallback(
    async (audioBlob) => {
      if (submittingRef.current || !state.result) {
        return;
      }

      submittingRef.current = true;
      setState((current) => ({
        ...current,
        status: "confirming",
        errorMessage: null,
      }));

      try {
        const confirmationResult =
          await confirmVoiceRecording(audioBlob);

        const confirmation = confirmationResult.confirmation;
        const language = state.result.assistant_response.language;

        setState((current) => ({
          ...current,
          confirmation,
          conversation: [
            ...current.conversation,
            { role: "user", text: confirmationResult.transcript },
          ],
        }));

        if (confirmation === "CONFIRMED") {
          setState((current) => ({
            ...current,
            status: "saving",
          }));

          await createServiceRequests(
            state.result.raw_input.id,
            state.result.extraction.tasks,
          );

          setState((current) => ({
            ...current,
            status: "speaking",
            errorMessage: null,
            conversation: [
              ...current.conversation,
              {
                role: "assistant",
                text: "Your requests have been confirmed and sent to the hotel team.",
              },
            ],
          }));

          try {
            await speak(
              "Your requests have been confirmed and sent to the hotel team.",
              language,
            );
          } catch (error) {
            setState((current) => ({
              ...current,
              status: "complete",
              errorMessage:
                error instanceof Error
                  ? `Speech playback failed: ${error.message}`
                  : "Speech playback failed.",
            }));
            return;
          }

          setState((current) => ({ ...current, status: "complete" }));
        } else if (confirmation === "DECLINED") {
          setState((current) => ({
            ...current,
            status: "speaking",
            errorMessage: null,
            conversation: [
              ...current.conversation,
              { role: "assistant", text: "Okay, I won't send those requests." },
            ],
          }));

          try {
            await speak("Okay, I won't send those requests.", language);
          } catch (error) {
            setState((current) => ({
              ...current,
              status: "declined",
              errorMessage:
                error instanceof Error
                  ? `Speech playback failed: ${error.message}`
                  : "Speech playback failed.",
            }));
            return;
          }

          setState((current) => ({ ...current, status: "declined" }));
        } else {
          setState((current) => ({
            ...current,
            status: "speaking",
            conversation: [
              ...current.conversation,
              {
                role: "assistant",
                text: "Sorry, I didn't catch that. Please say yes to confirm or no to cancel.",
              },
            ],
          }));

          try {
            await speak(
              "Sorry, I didn't catch that. Please say yes to confirm or no to cancel.",
              language,
            );
          } catch (error) {
            setState((current) => ({
              ...current,
              status: "awaiting_confirmation",
              errorMessage:
                error instanceof Error
                  ? `Speech playback failed: ${error.message}`
                  : "Speech playback failed.",
            }));
            return;
          }

          setState((current) => ({
            ...current,
            status: "awaiting_confirmation",
          }));
        }
      } catch (error) {
        setState((current) => ({
          ...current,
          status: "awaiting_confirmation",
          errorMessage:
            error instanceof Error
              ? error.message
              : "Confirmation processing failed.",
        }));
      } finally {
        submittingRef.current = false;
      }
    },
    [speak, state.result],
  );

  return {
    ...state,
    reset,
    playResponse,
    submitRecording,
    submitConfirmation,
  };
}
