
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
};

export function useVoiceIngestion() {
  const [state, setState] = useState(INITIAL_STATE);
  const submittingRef = useRef(false);

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  const speak = useCallback(async (text, language) => {
    const audioBlob = await synthesizeSpeech({ text, language });
    await playAudioBlob(audioBlob);
  }, []);

  const submitRecording = useCallback(
    async (audioBlob) => {
      if (submittingRef.current) {
        return;
      }

      submittingRef.current = true;
      setState({
        ...INITIAL_STATE,
        status: "uploading",
      });

      try {
        const result = await ingestVoiceRecording(audioBlob);

        setState({
          status: "awaiting_confirmation",
          errorMessage: null,
          result,
          confirmation: null,
        });

        try {
          await speak(
            result.assistant_response.text,
            result.assistant_response.language,
          );
        } catch (error) {
          setState((current) => ({
            ...current,
            errorMessage:
              error instanceof Error
                ? `Speech playback failed: ${error.message}`
                : "Speech playback failed.",
          }));
        }
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

        setState((current) => ({
          ...current,
          confirmation,
        }));

        const language = state.result.assistant_response.language;

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
            status: "complete",
            errorMessage: null,
          }));

          await speak(
            "Your requests have been confirmed and sent to the hotel team.",
            language,
          );
        } else if (confirmation === "DECLINED") {
          setState((current) => ({
            ...current,
            status: "declined",
            errorMessage: null,
          }));

          await speak("Okay, I won't send those requests.", language);
        } else {
          setState((current) => ({
            ...current,
            status: "awaiting_confirmation",
          }));

          await speak(
            "Sorry, I didn't catch that. Please say yes to confirm or no to cancel.",
            language,
          );
        }
      } catch (error) {
        setState((current) => ({
          ...current,
          status:
            current.status === "saving"
              ? "awaiting_confirmation"
              : "awaiting_confirmation",
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
    submitRecording,
    submitConfirmation,
  };
}
