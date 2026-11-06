
let stopActivePlayback;

export async function playAudioBlob(audioBlob, { signal } = {}) {
  if (signal?.aborted) {
    return;
  }

  stopActivePlayback?.();
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);

  let handleEnded;
  let handleError;
  let handleAbort;
  let settlePlayback;

  try {
    const playbackPromise = new Promise((resolve, reject) => {
      settlePlayback = resolve;
      handleEnded = resolve;
      handleError = () =>
        reject(audio.error ?? new Error("Audio playback failed."));
      handleAbort = () => {
        audio.pause();
        resolve();
      };

      audio.addEventListener("ended", handleEnded, { once: true });
      audio.addEventListener("error", handleError, { once: true });
      signal?.addEventListener("abort", handleAbort, { once: true });
    });

    if (signal?.aborted) {
      handleAbort();
      await playbackPromise;
      return;
    }

    stopActivePlayback = handleAbort;
    await Promise.race([
      audio.play().then(() => playbackPromise),
      playbackPromise,
    ]);
  } finally {
    audio.removeEventListener("ended", handleEnded);
    audio.removeEventListener("error", handleError);
    signal?.removeEventListener("abort", handleAbort);
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
    URL.revokeObjectURL(audioUrl);
    if (stopActivePlayback === handleAbort) {
      stopActivePlayback = undefined;
    }
    settlePlayback?.();
  }
}
