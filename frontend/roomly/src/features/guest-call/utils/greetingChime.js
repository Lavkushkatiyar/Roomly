export async function playGreetingChime({ signal } = {}) {
  if (signal?.aborted) {
    return;
  }

  const audio = new Audio("/audio/ringing.mp3");
  audio.loop = true;
  audio.preload = "auto";
  audio.volume = 0.55;

  let handleAbort;
  let handleError;

  try {
    const playback = new Promise((resolve, reject) => {
      handleAbort = resolve;
      handleError = () =>
        reject(audio.error ?? new Error("Greeting ring playback failed."));
      signal?.addEventListener("abort", handleAbort, { once: true });
      audio.addEventListener("error", handleError, { once: true });
    });

    if (signal?.aborted) {
      return;
    }

    await Promise.race([audio.play(), playback]);
    if (signal?.aborted) {
      return;
    }

    await playback;
  } finally {
    signal?.removeEventListener("abort", handleAbort);
    audio.removeEventListener("error", handleError);
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
  }
}
