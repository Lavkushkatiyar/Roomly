import { useCallback, useRef, useState } from "react";

import { ingestVoiceRecording } from "../api/voiceIngestion";
import { synthesizeSpeech } from "../api/text_to_voice";
import { playAudioBlob } from "../utils/audioPlayback";

const INITIAL_STATE = {
  status: "idle",
  errorMessage: null,
  result: null,
};

export function useVoiceIngestion() {
  const [state, setState] = useState(INITIAL_STATE);
  const submittingRef = useRef(false);

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  const submitRecording = useCallback(async (audioBlob) => {
    if (submittingRef.current) {
      return;
    }

    submittingRef.current = true;
    setState({ status: "uploading", errorMessage: null, result: null });

    try {
      const result = await ingestVoiceRecording(audioBlob);
      setState({ status: "complete", errorMessage: null, result });

      const speechBlob = await synthesizeSpeech(result.assistant_response);
      await playAudioBlob(speechBlob);
    } catch (error) {
      setState((current) => ({
        ...current,
        errorMessage:
          error instanceof Error ? error.message : "Voice processing failed.",
      }));
    } finally {
      submittingRef.current = false;
    }
  }, []);

  return {
    ...state,
    reset,
    submitRecording,
  };
}
