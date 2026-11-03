
export async function playAudioBlob(audioBlob) {
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);

  let handleEnded;
  let handleError;

  try {
    const playbackPromise = new Promise((resolve, reject) => {
      handleEnded = resolve;
      handleError = () =>
        reject(audio.error ?? new Error("Audio playback failed."));

      audio.addEventListener("ended", handleEnded, { once: true });
      audio.addEventListener("error", handleError, { once: true });
    });

    await audio.play();
    await playbackPromise;
  } finally {
    audio.removeEventListener("ended", handleEnded);
    audio.removeEventListener("error", handleError);
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
    URL.revokeObjectURL(audioUrl);
  }
}
