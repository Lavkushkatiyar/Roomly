import { useCallback, useEffect, useRef, useState } from "react";

import { AudioWaveform } from "./AudioWaveform";
import { CallStatus } from "./CallStatus";
import { GreetingSection } from "./GreetingSection";
import { IngestionResults } from "./IngestionResults";
import { VoiceControl } from "./VoiceControl";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useConversationTurn } from "../hooks/useConversationTurn";
import { useServiceRequests } from "../hooks/useServiceRequests";
import { playAudioBlob } from "../utils/audioPlayback";
import { playGreetingChime } from "../utils/greetingChime";
import { synthesizeNaturalMessage } from "../utils/naturalSpeech";
import "./guest-call.css";

const MINIMUM_GREETING_RING_MS = 600;

function formatRequestLabel(value) {
  return value
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatRequestTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Submission time unavailable";
  }

  return `Submitted ${date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  })}`;
}

export function GuestCallScreen({ roomId, guestLanguage }) {
  const [isGreeting, setIsGreeting] = useState(false);
  const [greetingError, setGreetingError] = useState(null);
  const greetingControllerRef = useRef(null);
  const greetingAudioRef = useRef(null);
  const greetingSynthesisRef = useRef(null);
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
    requests,
    status: requestsStatus,
    errorMessage: requestsError,
    reload: reloadRequests,
  } = useServiceRequests(roomId);
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
    onConfirmed: reloadRequests,
  });
  const submittedBlobRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    const synthesis = synthesizeNaturalMessage(guestLanguage, "greeting", {
      signal: controller.signal,
    });
    greetingSynthesisRef.current = synthesis;
    synthesis
      .then((audio) => {
        if (!controller.signal.aborted) {
          greetingAudioRef.current = audio;
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          console.warn("Could not prepare the guest greeting.", error);
        }
      })
      .finally(() => {
        if (greetingSynthesisRef.current === synthesis) {
          greetingSynthesisRef.current = null;
        }
      });

    return () => {
      controller.abort();
      greetingAudioRef.current = null;
      if (greetingSynthesisRef.current === synthesis) {
        greetingSynthesisRef.current = null;
      }
      greetingControllerRef.current?.abort();
    };
  }, [guestLanguage]);

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

    const ringController = new AbortController();
    const ringStartedAt = performance.now();
    const ringPlayback = playGreetingChime({
      signal: ringController.signal,
    }).catch((error) => {
      if (!ringController.signal.aborted) {
        console.warn("Could not play the greeting ring.", error);
      }
    });
    let greetingAudio;
    try {
      greetingAudio = greetingAudioRef.current;
      if (!greetingAudio && greetingSynthesisRef.current) {
        try {
          greetingAudio = await greetingSynthesisRef.current;
        } catch {
          if (controller.signal.aborted) {
            return;
          }
        }
      }

      if (!greetingAudio && !controller.signal.aborted) {
        greetingAudio = await synthesizeNaturalMessage(
          guestLanguage,
          "greeting",
          { signal: controller.signal },
        );
      }

      if (greetingAudio && !controller.signal.aborted) {
        greetingAudioRef.current = greetingAudio;
      }
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }

      setGreetingError(
        error instanceof Error
          ? `Greeting playback failed: ${error.message}`
          : "Greeting playback failed.",
      );
    } finally {
      const remainingRingDuration =
        MINIMUM_GREETING_RING_MS - (performance.now() - ringStartedAt);
      if (remainingRingDuration > 0 && !controller.signal.aborted) {
        await new Promise((resolve) =>
          window.setTimeout(resolve, remainingRingDuration),
        );
      }
      ringController.abort();
      await ringPlayback;
    }

    if (controller.signal.aborted) {
      return;
    }

    if (greetingAudio) {
      try {
        await playAudioBlob(greetingAudio, { signal: controller.signal });
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
    }

    if (controller.signal.aborted) {
      return;
    }

    setIsGreeting(false);
    await startRecording();
  }, [guestLanguage, startRecording]);

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
        <section
          className="guest-call__interaction"
          id="voice-dial"
          aria-label="Voice call"
        >
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
            id="guest-requests"
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
            {requestsStatus === "loading" && (
              <div className="guest-call__activity-card" role="status">
                <p>Loading your requests…</p>
              </div>
            )}
            {requestsStatus === "error" && (
              <div className="guest-call__activity-card">
                <p role="alert">{requestsError}</p>
                <button
                  className="guest-call__requests-retry"
                  type="button"
                  onClick={() => void reloadRequests()}
                >
                  Try again
                </button>
              </div>
            )}
            {requestsStatus === "loaded" && requests.length === 0 && (
              <div className="guest-call__activity-card">
                <p>No confirmed requests for this room yet.</p>
              </div>
            )}
            {requestsStatus === "loaded" && requests.length > 0 && (
              <div className="guest-call__request-list">
                {requests.map((request) => (
                  <article
                    className="guest-call__activity-card guest-call__request-card"
                    key={request.id}
                  >
                    <div className="guest-call__request-meta">
                      <span className="guest-call__request-category">
                        {formatRequestLabel(request.category)}
                      </span>
                      <span
                        className={`guest-call__request-status guest-call__request-status--${request.status.toLowerCase()}`}
                      >
                        {formatRequestLabel(request.status)}
                      </span>
                    </div>
                    <p className="guest-call__request-summary">
                      {request.staff_summary}
                    </p>
                    <time
                      className="guest-call__request-time"
                      dateTime={request.created_at}
                    >
                      {formatRequestTime(request.created_at)}
                    </time>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
