import { useEffect, useRef } from "react";

import { AudioWaveform } from "./AudioWaveform";
import { CallStatus } from "./CallStatus";
import { GreetingSection } from "./GreetingSection";
import { IngestionResults } from "./IngestionResults";
import { VoiceControl } from "./VoiceControl";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useVoiceIngestion } from "../hooks/useVoiceIngestion";
import "./guest-call.css";

export function GuestCallScreen() {
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
    reset: resetIngestion,
    submitRecording,
  } = useVoiceIngestion();
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
    void submitRecording(audioBlob);
  }, [audioBlob, recorderStatus, submitRecording]);

  const toggleRecording = () => {
    if (recorderStatus === "recording") {
      stopRecording();
      return;
    }

    if (ingestionStatus === "uploading") {
      return;
    }

    if (ingestionStatus === "error" && audioBlob) {
      void submitRecording(audioBlob);
      return;
    }

    submittedBlobRef.current = null;
    resetIngestion();
    void startRecording();
  };

  const status =
    ingestionStatus === "uploading" ||
    ingestionStatus === "complete" ||
    ingestionStatus === "error"
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
            disabled={ingestionStatus === "uploading"}
            retryUpload={ingestionStatus === "error" && Boolean(audioBlob)}
          />
          <AudioWaveform active={status === "recording"} />
          <CallStatus
            status={status}
            errorMessage={errorMessage}
            retrying={ingestionStatus === "error" && Boolean(audioBlob)}
          />
        </section>
        <IngestionResults result={result} />
      </div>
    </main>
  );
}
