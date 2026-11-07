const STATUS_LABELS = {
  idle: "Tap to start your call",
  greeting: "Welcome to ROOMLY",
  requesting: "Requesting microphone access",
  recording: "Listening · Tap stop to send your request",
  processing: "Finishing your recording",
  recorded: "Recording complete",
  uploading: "Sending your recording",
  acknowledging: "Just a moment, please",
  speaking: "Roomly is speaking",
  awaiting_clarification: "Tap the microphone to clarify your request",
  awaiting_confirmation: "Tap the microphone and say yes or no",
  confirming: "Checking your confirmation",
  saving: "Sending confirmed requests",
  complete: "Transcript and tasks ready",
  conversation_ended: "Conversation ended · Tap to start again",
  declined: "Requests cancelled",
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
      {status === "recording" && (
        <p className="call-status__hint">
          When you’re finished speaking, tap the square button. We’ll send your
          request automatically.
        </p>
      )}
      {errorMessage && (
        <div className="call-status__error" role="alert">
          <p>{errorMessage}</p>
          {retrying && <p>Tap the microphone to retry this recording.</p>}
        </div>
      )}
    </div>
  );
}
