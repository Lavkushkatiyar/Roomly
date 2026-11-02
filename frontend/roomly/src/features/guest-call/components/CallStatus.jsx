const STATUS_LABELS = {
  idle: "Tap to start your call",
  requesting: "Requesting microphone access",
  recording: "Listening · Tap to end your call",
  processing: "Finishing your recording",
  recorded: "Recording complete",
  uploading: "Sending your recording",
  complete: "Transcript and tasks ready",
  error: "Unable to complete request",
};

export function CallStatus({ status, errorMessage, retrying = false }) {
  return (
    <div className="call-status">
      <p className="call-status__label" aria-live="polite">
        {status === "recording" && (
          <span className="call-status__indicator" aria-hidden="true" />
        )}
        {STATUS_LABELS[status]}
      </p>
      {errorMessage && (
        <div className="call-status__error" role="alert">
          <p>{errorMessage}</p>
          {retrying && <p>Tap the microphone to retry this recording.</p>}
        </div>
      )}
    </div>
  );
}
