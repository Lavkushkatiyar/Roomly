import { useEffect, useRef, useState } from "react";

import "./guest-onboarding-modal.css";

function getMicrophoneReadiness(permissionState, hasInputDevice) {
  if (permissionState === "denied") {
    return {
      state: "error",
      label: "Microphone access is blocked in browser settings",
    };
  }

  if (permissionState === "granted") {
    return hasInputDevice
      ? { state: "ready", label: "Microphone ready" }
      : { state: "error", label: "No microphone detected" };
  }

  if (permissionState === "prompt") {
    return hasInputDevice
      ? { state: "waiting", label: "Microphone detected · access needed" }
      : {
          state: "waiting",
          label: "Microphone access will be checked when you begin",
        };
  }

  return hasInputDevice
    ? { state: "waiting", label: "Microphone detected" }
    : {
        state: "waiting",
        label: "Microphone readiness will be checked when you begin",
      };
}

function useMicrophoneReadiness() {
  const [readiness, setReadiness] = useState({
    state: "checking",
    label: "Checking microphone status",
  });

  useEffect(() => {
    let active = true;
    let permissionStatus;
    const mediaDevices = navigator.mediaDevices;

    const updateReadiness = async () => {
      if (!mediaDevices?.getUserMedia) {
        setReadiness({
          state: "error",
          label: "Microphone recording is not supported by this browser",
        });
        return;
      }

      let permissionState = "unknown";
      if (navigator.permissions?.query) {
        try {
          permissionStatus = await navigator.permissions.query({
            name: "microphone",
          });
          permissionState = permissionStatus.state;
          permissionStatus.onchange = updateReadiness;
        } catch {
          permissionState = "unknown";
        }
      }

      try {
        const devices = await mediaDevices.enumerateDevices();
        const hasInputDevice = devices.some(
          (device) => device.kind === "audioinput",
        );
        if (active) {
          setReadiness(
            getMicrophoneReadiness(permissionState, hasInputDevice),
          );
        }
      } catch {
        if (active) {
          setReadiness({
            state: permissionState === "denied" ? "error" : "waiting",
            label:
              permissionState === "denied"
                ? "Microphone access is blocked in browser settings"
                : "Microphone readiness will be checked when you begin",
          });
        }
        return;
      }
    };

    void updateReadiness();

    return () => {
      active = false;
      if (permissionStatus) {
        permissionStatus.onchange = null;
      }
    };
  }, []);

  return readiness;
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
  onBegin,
  videoSrc = null,
}) {
  const [doNotShowAgain, setDoNotShowAgain] = useState(false);
  const closeButtonRef = useRef(null);
  const rememberedChoiceRef = useRef(doNotShowAgain);
  const readiness = useMicrophoneReadiness();

  useEffect(() => {
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onSkip(rememberedChoiceRef.current);
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
    const dialog = document.querySelector(".guest-onboarding__dialog");
    dialog?.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      dialog?.removeEventListener("keydown", handleKeyDown);
      if (previousFocus instanceof HTMLElement) {
        previousFocus.focus();
      }
    };
  }, [onSkip]);

  return (
    <div className="guest-onboarding__overlay">
      <section
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
            onClick={() => onSkip(doNotShowAgain)}
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
          <span
            className={`guest-onboarding__mic-status guest-onboarding__mic-status--${readiness.state}`}
            role="status"
          >
            <span aria-hidden="true" />
            {readiness.label}
          </span>
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
              onClick={() => onSkip(doNotShowAgain)}
            >
              Skip
            </button>
            <button
              className="guest-onboarding__begin"
              type="button"
              onClick={() => onBegin(doNotShowAgain)}
            >
              Begin Voice Dial
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
        <p className="guest-onboarding__permission-note">
          Microphone access is only requested when you begin voice interaction.
        </p>
      </section>
    </div>
  );
}
