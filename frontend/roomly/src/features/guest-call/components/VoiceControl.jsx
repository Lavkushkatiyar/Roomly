export function VoiceControl({
  status,
  onToggle,
  disabled = false,
  retryUpload = false,
}) {
  const isRecording = status === "recording";
  const isBusy =
    status === "greeting" ||
    status === "acknowledging" ||
    status === "requesting" ||
    status === "processing" ||
    status === "uploading" ||
    status === "speaking" ||
    status === "confirming" ||
    status === "saving";
  const label = isRecording
    ? "End voice recording"
    : status === "awaiting_clarification"
      ? "Speak your clarification"
      : status === "awaiting_confirmation"
        ? "Speak yes or no to confirm"
    : status === "complete"
      ? "Record another message"
      : status === "error"
        ? retryUpload
          ? "Retry voice request"
          : "Retry microphone access"
        : "Start voice recording";

  return (
    <div
      className={`voice-control${isRecording ? " voice-control--recording" : ""}`}
    >
      <span className="voice-control__ring voice-control__ring--outer" />
      <span className="voice-control__ring voice-control__ring--inner" />
      <button
        className="voice-control__button"
        type="button"
        onClick={onToggle}
        disabled={isBusy || disabled}
        aria-label={label}
        aria-pressed={isRecording}
      >
        {isRecording ? (
          <svg
            aria-hidden="true"
            className="voice-control__stop-icon"
            viewBox="0 0 24 24"
          >
            <rect x="7" y="7" width="10" height="10" rx="1" />
          </svg>
        ) : (
          <svg
            aria-hidden="true"
            className="voice-control__mic-icon"
            viewBox="0 0 24 24"
            fill="none"
          >
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
        )}
      </button>
    </div>
  );
}
