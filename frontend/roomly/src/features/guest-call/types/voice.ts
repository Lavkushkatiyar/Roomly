export type RecorderStatus =
  | "idle"
  | "requesting"
  | "recording"
  | "processing"
  | "recorded"
  | "error";

export interface AudioRecorderState {
  status: RecorderStatus;
  errorMessage: string | null;
  audioBlob: Blob | null;
}
