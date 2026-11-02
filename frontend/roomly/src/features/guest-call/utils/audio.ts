const SUPPORTED_AUDIO_TYPES = [
  "audio/webm;codecs=opus",
  "audio/mp4",
  "audio/webm",
  "audio/ogg;codecs=opus",
];

export function getSupportedAudioMimeType(): string | null {
  if (typeof MediaRecorder.isTypeSupported !== "function") {
    return null;
  }

  return (
    SUPPORTED_AUDIO_TYPES.find((mimeType) =>
      MediaRecorder.isTypeSupported(mimeType),
    ) ?? null
  );
}

export function stopMediaStream(stream: MediaStream | null): void {
  stream?.getTracks().forEach((track) => track.stop());
}

export function getRecordingErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError" || error.name === "SecurityError") {
      return "Microphone access was denied. Allow access in your browser settings and try again.";
    }

    if (error.name === "NotFoundError") {
      return "No microphone was found. Connect a microphone and try again.";
    }

    if (error.name === "NotReadableError" || error.name === "AbortError") {
      return "The microphone could not be started. Check that it is not in use by another app.";
    }
  }

  return "Recording could not be started. Please try again.";
}
