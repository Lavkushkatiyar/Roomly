import { useCallback, useEffect, useRef, useState } from "react";

import { submitConversationTurn } from "../api/conversationTurn";
import { playAudioBlob } from "../utils/audioPlayback";
import { playNaturalMessage } from "../utils/naturalSpeech";

const INITIAL_STATE = {
  status: "idle",
  errorMessage: null,
  result: null,
  speechBlob: null,
  conversation: [],
};

function getReadyStatus(result) {
  if (result.conversation_ended) {
    return "conversation_ended";
  }

  const { turn } = result;
  if (turn.intent === "CONFIRMATION") {
    return "complete";
  }
  if (turn.intent === "REJECTION") {
    return "declined";
  }
  if (
    (turn.intent === "NEW_REQUEST" || turn.intent === "MODIFICATION") &&
    turn.tasks.length > 0
  ) {
    return "awaiting_confirmation";
  }
  return "awaiting_clarification";
}

export function useConversationTurn({
  roomId,
  guestLanguage,
  onResponseFinished,
}) {
  const [state, setState] = useState(INITIAL_STATE);
  const submittingRef = useRef(false);
  const conversationIdRef = useRef(null);
  const speechBlobRef = useRef(null);
  const mountedRef = useRef(false);
  const playbackControllersRef = useRef(new Set());

  const createPlaybackController = useCallback(() => {
    const controller = new AbortController();
    playbackControllersRef.current.add(controller);
    controller.signal.addEventListener(
      "abort",
      () => playbackControllersRef.current.delete(controller),
      { once: true },
    );
    return controller;
  }, []);

  useEffect(() => {
    const playbackControllers = playbackControllersRef.current;
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      playbackControllers.forEach((controller) => controller.abort());
      playbackControllers.clear();
    };
  }, []);

  const submitRecording = useCallback(
    async (audioBlob) => {
      if (submittingRef.current) {
        return;
      }

      submittingRef.current = true;
      speechBlobRef.current = null;
      const acknowledgementController = createPlaybackController();
      let acknowledgementTimer;
      setState((current) => ({
        ...current,
        status: "uploading",
        errorMessage: null,
        speechBlob: null,
      }));

      try {
        acknowledgementTimer = window.setTimeout(() => {
          if (!mountedRef.current || acknowledgementController.signal.aborted) {
            return;
          }

          setState((current) => ({ ...current, status: "acknowledging" }));
          void playNaturalMessage(guestLanguage, "processing", {
            signal: acknowledgementController.signal,
          })
            .catch((error) => {
              if (
                !acknowledgementController.signal.aborted &&
                mountedRef.current
              ) {
                setState((current) => ({
                  ...current,
                  errorMessage:
                    error instanceof Error
                      ? `Processing acknowledgement failed: ${error.message}`
                      : "Processing acknowledgement failed.",
                }));
              }
            })
            .finally(() => {
              playbackControllersRef.current.delete(acknowledgementController);
            });
        }, 700);

        const result = await submitConversationTurn(audioBlob, {
          roomId,
          guestLanguage,
          conversationId: conversationIdRef.current,
        });
        window.clearTimeout(acknowledgementTimer);
        acknowledgementController.abort();

        if (!mountedRef.current) {
          return;
        }

        conversationIdRef.current = result.conversation_ended
          ? null
          : result.conversation_id;
        speechBlobRef.current = result.speechBlob;
        const readyStatus = getReadyStatus(result);

        setState((current) => ({
          ...current,
          status: "speaking",
          errorMessage: null,
          result,
          speechBlob: result.speechBlob,
          conversation: [
            ...current.conversation,
            { role: "user", text: result.raw_input.transcript },
            { role: "assistant", text: result.turn.assistant_response.text },
          ],
        }));

        const responseController = createPlaybackController();
        try {
          await playAudioBlob(result.speechBlob, {
            signal: responseController.signal,
          });
        } catch (error) {
          if (!responseController.signal.aborted) {
            setState((current) => ({
              ...current,
              status: readyStatus,
              errorMessage:
                error instanceof Error
                  ? `Speech playback failed: ${error.message}`
                  : "Speech playback failed.",
            }));
            return;
          }
        } finally {
          playbackControllersRef.current.delete(responseController);
        }

        if (responseController.signal.aborted || !mountedRef.current) {
          return;
        }

        setState((current) => ({ ...current, status: readyStatus }));
        if (!result.conversation_ended) {
          submittingRef.current = false;
          await onResponseFinished?.();
        }
      } catch (error) {
        if (mountedRef.current) {
          setState((current) => ({
            ...current,
            status: "error",
            errorMessage:
              error instanceof Error
                ? error.message
                : "Conversation processing failed.",
          }));
        }
      } finally {
        window.clearTimeout(acknowledgementTimer);
        acknowledgementController.abort();
        playbackControllersRef.current.delete(acknowledgementController);
        submittingRef.current = false;
      }
    },
    [createPlaybackController, guestLanguage, onResponseFinished, roomId],
  );

  const playResponse = useCallback(async () => {
    const speechBlob = speechBlobRef.current;
    if (!speechBlob) {
      return;
    }

    const playbackController = createPlaybackController();
    try {
      await playAudioBlob(speechBlob, {
        signal: playbackController.signal,
      });
      if (mountedRef.current && !playbackController.signal.aborted) {
        setState((current) => ({ ...current, errorMessage: null }));
      }
    } catch (error) {
      if (mountedRef.current && !playbackController.signal.aborted) {
        setState((current) => ({
          ...current,
          errorMessage:
            error instanceof Error
              ? `Speech playback failed: ${error.message}`
              : "Speech playback failed.",
        }));
      }
    } finally {
      playbackControllersRef.current.delete(playbackController);
    }
  }, [createPlaybackController]);

  return {
    ...state,
    submitRecording,
    playResponse,
  };
}
