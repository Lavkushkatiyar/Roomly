import { useCallback, useEffect, useRef, useState } from "react";

import {
  getRecordingErrorMessage,
  getSupportedAudioMimeType,
  stopMediaStream,
} from "../utils/audio";

const INITIAL_STATE = {
  status: "idle",
  errorMessage: null,
  audioBlob: null,
};

function getUnsupportedErrorMessage() {
  if (!navigator.mediaDevices?.getUserMedia) {
    return "Microphone recording is not supported by this browser. Try a current browser over a secure connection.";
  }

  if (typeof MediaRecorder === "undefined") {
    return "Audio recording is not supported by this browser. Try a current browser.";
  }

  return "This browser does not support a recording format we can use.";
}

export function useAudioRecorder() {
  const [state, setState] = useState(INITIAL_STATE);
  const mountedRef = useRef(false);
  const startingRef = useRef(false);
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const recorderFailedRef = useRef(false);

  const updateState = useCallback((nextState) => {
    if (mountedRef.current) {
      setState(nextState);
    }
  }, []);

  const failRecording = useCallback(
    (message) => {
      recorderFailedRef.current = true;
      recorderRef.current = null;
      stopMediaStream(streamRef.current);
      streamRef.current = null;
      chunksRef.current = [];
      updateState({
        status: "error",
        errorMessage: message,
        audioBlob: null,
      });
    },
    [updateState],
  );

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      const recorder = recorderRef.current;
      recorderRef.current = null;

      if (recorder) {
        recorder.ondataavailable = null;
        recorder.onerror = null;
        recorder.onstop = null;

        if (recorder.state !== "inactive") {
          recorder.stop();
        }
      }

      stopMediaStream(streamRef.current);
      streamRef.current = null;
      chunksRef.current = [];
    };
  }, []);

  const startRecording = useCallback(async () => {
    if (startingRef.current || recorderRef.current?.state === "recording") {
      return;
    }

    startingRef.current = true;
    recorderFailedRef.current = false;
    updateState({
      status: "requesting",
      errorMessage: null,
      audioBlob: null,
    });

    let stream = null;

    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
        failRecording(getUnsupportedErrorMessage());
        return;
      }

      const mimeType = getSupportedAudioMimeType();
      if (!mimeType) {
        failRecording(getUnsupportedErrorMessage());
        return;
      }

      stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      if (!mountedRef.current) {
        stopMediaStream(stream);
        return;
      }

      streamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream, { mimeType });
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        failRecording("Recording was interrupted. Please try again.");
      };

      recorder.onstop = () => {
        stopMediaStream(streamRef.current);
        streamRef.current = null;
        recorderRef.current = null;

        if (recorderFailedRef.current) {
          return;
        }

        const audioBlob = new Blob(chunksRef.current, { type: mimeType });
        chunksRef.current = [];

        if (audioBlob.size === 0) {
          failRecording("No audio was captured. Please try recording again.");
          return;
        }

        updateState({
          status: "recorded",
          errorMessage: null,
          audioBlob,
        });
      };

      recorder.start();
      updateState({
        status: "recording",
        errorMessage: null,
        audioBlob: null,
      });
    } catch (error) {
      if (stream) {
        stopMediaStream(stream);
      }
      streamRef.current = null;
      failRecording(getRecordingErrorMessage(error));
    } finally {
      startingRef.current = false;
    }
  }, [failRecording, updateState]);

  const stopRecording = useCallback(() => {
    const recorder = recorderRef.current;

    if (!recorder || recorder.state !== "recording") {
      return;
    }

    updateState({
      status: "processing",
      errorMessage: null,
      audioBlob: null,
    });

    try {
      recorder.stop();
    } catch (error) {
      const message =
        error instanceof DOMException && error.name === "InvalidStateError"
          ? "The recording has already stopped. Please try again."
          : "Recording could not be completed. Please try again.";
      failRecording(message);
    }
  }, [failRecording, updateState]);

  return {
    ...state,
    startRecording,
    stopRecording,
  };
}
