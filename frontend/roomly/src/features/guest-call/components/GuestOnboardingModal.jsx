import { useCallback, useEffect, useRef, useState } from "react";

import "./guest-onboarding-modal.css";

function getMicrophoneReadiness(permissionState, hasInputDevice) {
  if (permissionState === "denied") {
    return {
      state: "error",
      permissionState,
      label: "Microphone access is blocked in browser settings",
    };
  }

  if (permissionState === "granted") {
    return hasInputDevice
      ? { state: "ready", permissionState, label: "Microphone ready" }
      : {
          state: "error",
          permissionState,
          label: "No microphone detected",
        };
  }

  if (permissionState === "prompt") {
    return hasInputDevice
      ? {
          state: "waiting",
          permissionState,
          label: "Microphone detected · access needed",
        }
      : {
          state: "waiting",
          permissionState,
          label: "Microphone access will be checked when you begin",
        };
  }

  return hasInputDevice
    ? { state: "waiting", permissionState, label: "Microphone detected" }
    : {
        state: "waiting",
        permissionState,
        label: "Microphone readiness will be checked when you begin",
      };
}

function useMicrophoneReadiness() {
  const [readiness, setReadiness] = useState({
    state: "checking",
    permissionState: "unknown",
    label: "Checking microphone status",
  });
  const [isRequesting, setIsRequesting] = useState(false);
  const permissionStatusRef = useRef(null);

  const refreshReadiness = useCallback(async () => {
    const mediaDevices = navigator.mediaDevices;

    if (!mediaDevices?.getUserMedia) {
      const unsupported = {
        state: "error",
        permissionState: "unknown",
        label: "Microphone recording is not supported by this browser",
      };
      setReadiness(unsupported);
      return unsupported;
    }

    let permissionState = "unknown";
    if (navigator.permissions?.query) {
      try {
        const permissionStatus = await navigator.permissions.query({
          name: "microphone",
        });
        permissionStatusRef.current = permissionStatus;
        permissionState = permissionStatus.state;
      } catch {
        permissionState = "unknown";
      }
    }

    try {
      const devices = await mediaDevices.enumerateDevices();
      const currentReadiness = getMicrophoneReadiness(
        permissionState,
        devices.some((device) => device.kind === "audioinput"),
      );
      setReadiness(currentReadiness);
      return currentReadiness;
    } catch {
      const currentReadiness = {
        state: permissionState === "denied" ? "error" : "waiting",
        permissionState,
        label:
          permissionState === "denied"
            ? "Microphone access is blocked in browser settings"
            : "Microphone readiness will be checked when you begin",
      };
      setReadiness(currentReadiness);
      return currentReadiness;
    }
  }, []);

  const requestMicrophoneAccess = useCallback(async () => {
    if (
      readiness.permissionState === "denied" ||
      !navigator.mediaDevices?.getUserMedia
    ) {
      return;
    }

    setIsRequesting(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const hasAudioTrack = stream.getAudioTracks().length > 0;
      stream.getTracks().forEach((track) => track.stop());

      if (hasAudioTrack) {
        setReadiness({
          state: "ready",
          permissionState: "granted",
          label: "Microphone ready",
        });
      } else {
        setReadiness({
          state: "error",
          permissionState: "granted",
          label: "No microphone detected",
        });
      }
    } catch (error) {
      const denied = ["NotAllowedError", "SecurityError"].includes(error?.name);
      const missing = error?.name === "NotFoundError";
      setReadiness({
        state: "error",
        permissionState: denied ? "denied" : readiness.permissionState,
        label: denied
          ? "Access blocked · allow microphone in browser settings"
          : missing
            ? "No microphone detected"
            : "Could not check microphone · try again",
      });
    } finally {
      setIsRequesting(false);
    }
  }, [readiness.permissionState]);

  useEffect(() => {
    let active = true;
    const updateReadiness = async () => {
      const currentReadiness = await refreshReadiness();
      if (!active) {
        return;
      }
      if (permissionStatusRef.current) {
        permissionStatusRef.current.onchange = () => {
          void refreshReadiness();
        };
      }
      return currentReadiness;
    };

    void updateReadiness();

    return () => {
      active = false;
      if (permissionStatusRef.current) {
        permissionStatusRef.current.onchange = null;
      }
    };
  }, [refreshReadiness]);

  return { readiness, isRequesting, requestMicrophoneAccess };
}

function DemoVideo({ src }) {
  if (src) {
    return (
      <video
        className="guest-onboarding__video"
        controls
        playsInline
        preload="metadata"
      >
        <source src={src} />
        Your browser does not support embedded video.
      </video>
    );
  }

  return (
    <div
      className="guest-onboarding__video-placeholder"
      role="group"
      aria-label="ROOMLY voice concierge walkthrough"
    >
      <p className="guest-onboarding__video-note">
        Demonstration video coming soon
      </p>
      <ol className="guest-onboarding__workflow">
        <li>Speak</li>
        <li>ROOMLY interprets</li>
        <li>Review and confirm</li>
        <li>Request is submitted</li>
        <li>Track your request</li>
      </ol>
    </div>
  );
}

export function GuestOnboardingModal({
  onSkip,
  onEnter,
  onClosed,
  errorMessage,
  videoSrc = null,
}) {
  const [doNotShowAgain, setDoNotShowAgain] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const closeButtonRef = useRef(null);
  const dialogRef = useRef(null);
  const closingRef = useRef(false);
  const dismissTimerRef = useRef(null);
  const rememberedChoiceRef = useRef(doNotShowAgain);
  const {
    readiness,
    isRequesting,
    requestMicrophoneAccess,
  } = useMicrophoneReadiness();
  const microphoneActionLabel = isRequesting
    ? "Checking…"
    : readiness.permissionState === "denied"
      ? "Permission blocked"
      : readiness.state === "error"
        ? readiness.label === "No microphone detected"
          ? "No microphone"
          : "Try again"
        : readiness.state === "ready"
          ? "Test microphone"
          : ["prompt", "unknown"].includes(readiness.permissionState)
            ? "Allow microphone"
            : "Check microphone";

  const dismiss = useCallback(
    (action, rememberChoice) => {
      if (closingRef.current || action(rememberChoice) === false) {
        return;
      }

      closingRef.current = true;
      setIsClosing(true);
      dismissTimerRef.current = window.setTimeout(onClosed, 220);
    },
    [onClosed],
  );

  useEffect(() => {
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        dismiss(onSkip, rememberedChoiceRef.current);
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const focusableElements = event.currentTarget.querySelectorAll(
        'button, input[type="checkbox"]',
      );
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    };

    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    const dialog = dialogRef.current;
    dialog?.addEventListener("keydown", handleKeyDown);

    return () => {
      window.clearTimeout(dismissTimerRef.current);
      document.body.style.overflow = previousOverflow;
      dialog?.removeEventListener("keydown", handleKeyDown);
      if (previousFocus instanceof HTMLElement) {
        previousFocus.focus();
      }
    };
  }, [dismiss, onSkip]);

  return (
    <div
      className={`guest-onboarding__overlay${isClosing ? " guest-onboarding__overlay--closing" : ""}`}
    >
      <section
        ref={dialogRef}
        className="guest-onboarding__dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="guest-onboarding-title"
        aria-describedby="guest-onboarding-description"
      >
        <div className="guest-onboarding__topline">
          <span className="guest-onboarding__eyebrow">
            Guest concierge orientation
          </span>
          <button
            ref={closeButtonRef}
            className="guest-onboarding__close"
            type="button"
            aria-label="Close orientation"
            onClick={() => dismiss(onSkip, doNotShowAgain)}
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="m6 6 12 12M18 6 6 18"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        <header className="guest-onboarding__header">
          <h1 id="guest-onboarding-title">
            Welcome to Your Voice Sanctuary.
          </h1>
          <p id="guest-onboarding-description">
            Talk naturally with ROOMLY, review what it understood, confirm your
            request, and follow its progress.
          </p>
        </header>

        <DemoVideo src={videoSrc} />

        <section
          className="guest-onboarding__prompt"
          aria-label="Example voice prompt"
        >
          <span className="guest-onboarding__prompt-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <rect
                x="9"
                y="3"
                width="6"
                height="12"
                rx="3"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3m-3 0h6"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </span>
          <div className="guest-onboarding__prompt-copy">
            <span className="guest-onboarding__prompt-label">
              Try saying
            </span>
            <p>“Could I have fresh towels, please?”</p>
          </div>
          <div className="guest-onboarding__mic-check">
            <button
              className={`guest-onboarding__mic-status guest-onboarding__mic-status--${readiness.state}`}
              type="button"
              disabled={
                isRequesting ||
                readiness.permissionState === "denied" ||
                !navigator.mediaDevices?.getUserMedia
              }
              onClick={() => void requestMicrophoneAccess()}
            >
              <span aria-hidden="true" />
              {microphoneActionLabel}
            </button>
            <p
              className="guest-onboarding__mic-detail"
              role={readiness.state === "error" ? "alert" : "status"}
            >
              {readiness.label}
            </p>
          </div>
        </section>

        <div className="guest-onboarding__actions">
          <label className="guest-onboarding__remember">
            <input
              checked={doNotShowAgain}
              onChange={(event) => {
                const checked = event.target.checked;
                rememberedChoiceRef.current = checked;
                setDoNotShowAgain(checked);
              }}
              type="checkbox"
            />
            <span>Do not show orientation again</span>
          </label>

          <div className="guest-onboarding__buttons">
            <button
              className="guest-onboarding__skip"
              type="button"
              onClick={() => dismiss(onSkip, doNotShowAgain)}
            >
              Skip
            </button>
            <button
              className="guest-onboarding__begin"
              type="button"
              onClick={() => dismiss(onEnter, doNotShowAgain)}
            >
              Enter App
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path
                  d="M3.5 10h12m-5-5 5 5-5 5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>
        {errorMessage && (
          <p className="guest-onboarding__error" role="alert">
            {errorMessage}
          </p>
        )}
        <p className="guest-onboarding__permission-note">
          Microphone access is only requested when you allow it here or begin
          voice interaction.
        </p>
      </section>
    </div>
  );
}
