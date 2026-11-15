import { useCallback, useEffect, useRef, useState } from "react";

import { AudioWaveform } from "./AudioWaveform";
import { CallStatus } from "./CallStatus";
import { GreetingSection } from "./GreetingSection";
import { IngestionResults } from "./IngestionResults";
import { VoiceControl } from "./VoiceControl";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useConversationTurn } from "../hooks/useConversationTurn";
import { playGreetingChime } from "../utils/greetingChime";
import { playNaturalMessage } from "../utils/naturalSpeech";
import "./guest-call.css";

export function GuestCallScreen({ roomId, guestLanguage, greetOnEntry = false }) {
  const [isGreeting, setIsGreeting] = useState(false);
  const [greetingError, setGreetingError] = useState(null);
  const greetingControllerRef = useRef(null);
  const conversationStartedRef = useRef(false);
  const {
    status: recorderStatus,
    errorMessage: recordingError,
    audioBlob,
    startRecording,
    stopRecording,
  } = useAudioRecorder();
  const startListeningAfterReply = useCallback(
    () => startRecording(),
    [startRecording],
  );
  const {
    status: ingestionStatus,
    errorMessage: ingestionError,
    result,
    speechBlob,
    submitRecording,
    playResponse,
  } = useConversationTurn({
    roomId,
    guestLanguage,
    onResponseFinished: startListeningAfterReply,
  });
  const submittedBlobRef = useRef(null);

  const startConversationWithGreeting = useCallback(async () => {
    if (conversationStartedRef.current) {
      return;
    }

    conversationStartedRef.current = true;
    greetingControllerRef.current?.abort();
    const controller = new AbortController();
    greetingControllerRef.current = controller;
    setIsGreeting(true);
    setGreetingError(null);

    try {
      await playGreetingChime({ signal: controller.signal });
      if (controller.signal.aborted) {
        return;
      }
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }

      console.warn("Could not play the greeting chime.", error);
    }

    try {
      await playNaturalMessage(guestLanguage, "greeting", {
        signal: controller.signal,
      });
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }
      setGreetingError(
        error instanceof Error
          ? `Greeting playback failed: ${error.message}`
          : "Greeting playback failed.",
      );
    }

    if (controller.signal.aborted) {
      return;
    }

    setIsGreeting(false);
    await startRecording();
  }, [guestLanguage, startRecording]);

  useEffect(() => {
    if (!greetOnEntry) {
      return undefined;
    }

    let cancelled = false;
    const timer = window.setTimeout(() => {
      if (!cancelled) {
        void startConversationWithGreeting();
      }
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      greetingControllerRef.current?.abort();
    };
  }, [greetOnEntry, startConversationWithGreeting]);

  useEffect(() => {
    if (ingestionStatus === "conversation_ended") {
      conversationStartedRef.current = false;
    }
  }, [ingestionStatus]);

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
  }, [
    audioBlob,
    recorderStatus,
    submitRecording,
  ]);

  const toggleRecording = () => {
    if (
      ingestionStatus === "conversation_ended" &&
      !conversationStartedRef.current
    ) {
      void startConversationWithGreeting();
      return;
    }

    setGreetingError(null);

    if (!conversationStartedRef.current) {
      void startConversationWithGreeting();
      return;
    }

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
      void submitRecording(audioBlob);
      return;
    }

    submittedBlobRef.current = null;
    void startRecording();
  };

  const recorderIsActive = [
    "requesting",
    "recording",
    "processing",
  ].includes(recorderStatus);
  const status = recorderIsActive
    ? recorderStatus
    : isGreeting
      ? "greeting"
      : ingestionStatus !== "idle"
        ? ingestionStatus
        : recorderStatus;
  const errorMessage = ingestionError ?? greetingError ?? recordingError;

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
              "acknowledging",
              "speaking",
              "confirming",
              "saving",
            ].includes(ingestionStatus) || isGreeting}
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
              disabled={
                recorderIsActive ||
                ["uploading", "acknowledging", "speaking"].includes(
                  ingestionStatus,
                )
              }
            >
              Play response
            </button>
          )}
        </section>
        <IngestionResults result={result} />
        <div className="guest-call__activity">
          <section
            className="guest-call__activity-section"
            aria-labelledby="guest-services-title"
          >
            <div className="guest-call__activity-heading">
              <span className="guest-call__activity-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M4 10.5 12 4l8 6.5V20H4v-9.5Z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M9 20v-6h6v6M8 10h.01M12 10h.01M16 10h.01"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </span>
              <h2
                className="guest-call__activity-title"
                id="guest-services-title"
              >
                Your Services
              </h2>
            </div>
            <div className="guest-call__activity-card">
              <p>
                The hotel service catalogue is not available yet. Please ask
                the concierge about available services.
              </p>
            </div>
          </section>

          <section
            className="guest-call__activity-section"
            aria-labelledby="guest-requests-title"
          >
            <div className="guest-call__activity-heading">
              <span className="guest-call__activity-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M6 4.5h12v15H6zM9 8h6M9 11.5h6M9 15h3"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <h2
                className="guest-call__activity-title"
                id="guest-requests-title"
              >
                Your Requests
              </h2>
            </div>
            <div className="guest-call__activity-card">
              <p>
                Request history for this room is not available yet. Your
                submitted requests will appear here when it is supported.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
