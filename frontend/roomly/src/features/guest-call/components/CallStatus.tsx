import type { RecorderStatus } from "../types/voice";

interface CallStatusProps {
  status: RecorderStatus;
  errorMessage: string | null;
}

const STATUS_LABELS: Record<RecorderStatus, string> = {
  idle: "Tap to start your call",
  requesting: "Requesting microphone access",
  recording: "Listening · Tap to end your call",
  processing: "Finishing your recording",
  recorded: "Recording complete",
  error: "Microphone unavailable",
};

export function CallStatus({ status, errorMessage }: CallStatusProps) {
  return (
    <div className="call-status">
      <p className="call-status__label" aria-live="polite">
        {status === "recording" && (
          <span className="call-status__indicator" aria-hidden="true" />
        )}
        {STATUS_LABELS[status]}
      </p>
      {errorMessage && (
        <p className="call-status__error" role="alert">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
