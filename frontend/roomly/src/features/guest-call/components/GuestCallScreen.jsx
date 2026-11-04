import { useEffect, useRef } from "react";

import { AudioWaveform } from "./AudioWaveform";
import { CallStatus } from "./CallStatus";
import { GreetingSection } from "./GreetingSection";
import { IngestionResults } from "./IngestionResults";
import { VoiceControl } from "./VoiceControl";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useVoiceIngestion } from "../hooks/useVoiceIngestion";
import "./guest-call.css";

export function GuestCallScreen({ roomId, guestLanguage }) {
  const {
    status: recorderStatus,
    errorMessage: recordingError,
    audioBlob,
    startRecording,
    stopRecording,
  } = useAudioRecorder();
  const {
    status: ingestionStatus,
    errorMessage: ingestionError,
    result,
    conversation,
    speechBlob,
    reset: resetIngestion,
    submitRecording,
    submitConfirmation,
    playResponse,
  } = useVoiceIngestion({ roomId, guestLanguage });
  const submittedBlobRef = useRef(null);

  useEffect(() => {
    if (
      recorderStatus !== "recorded" ||
      !audioBlob ||
      submittedBlobRef.current === audioBlob
    ) {
      return;
    }

    submittedBlobRef.current = audioBlob;
    if (ingestionStatus === "awaiting_confirmation") {
      void submitConfirmation(audioBlob);
    } else if (ingestionStatus === "awaiting_clarification") {
      void submitRecording(audioBlob, { continueConversation: true });
    } else {
      void submitRecording(audioBlob);
    }
  }, [
    audioBlob,
    ingestionStatus,
    recorderStatus,
    submitConfirmation,
    submitRecording,
  ]);

  const toggleRecording = () => {
    if (recorderStatus === "recording") {
      stopRecording();
      return;
    }

    if (
      ingestionStatus === "uploading" ||
      ingestionStatus === "speaking" ||
      ingestionStatus === "confirming" ||
      ingestionStatus === "saving"
    ) {
      return;
    }

    if (ingestionStatus === "error" && audioBlob) {
      void submitRecording(audioBlob, {
        continueConversation:
          result?.extraction.tasks.length === 0 && conversation.length > 0,
      });
      return;
    }

    submittedBlobRef.current = null;
    if (
      ingestionStatus !== "awaiting_clarification" &&
      ingestionStatus !== "awaiting_confirmation"
    ) {
      resetIngestion();
    }
    void startRecording();
  };

  const recorderIsActive = [
    "requesting",
    "recording",
    "processing",
  ].includes(recorderStatus);
  const status = recorderIsActive
    ? recorderStatus
    : ingestionStatus !== "idle"
      ? ingestionStatus
      : recorderStatus;
  const errorMessage = ingestionError ?? recordingError;

  return (
    <main className="guest-call" aria-labelledby="guest-call-title">
      <div className="guest-call__content">
        <GreetingSection />
        <section className="guest-call__interaction" aria-label="Voice call">
          <VoiceControl
            status={status}
            onToggle={toggleRecording}
            disabled={[
              "uploading",
              "speaking",
              "confirming",
              "saving",
            ].includes(ingestionStatus)}
            retryUpload={ingestionStatus === "error" && Boolean(audioBlob)}
          />
          <AudioWaveform active={status === "recording"} />
          <CallStatus
            status={status}
            errorMessage={errorMessage}
            retrying={ingestionStatus === "error" && Boolean(audioBlob)}
          />
          {speechBlob && (
            <button
              className="call-status__play"
              type="button"
              onClick={playResponse}
            >
              Play response
            </button>
          )}
        </section>
        <IngestionResults result={result} />
      </div>
    </main>
  );
}
