
export async function playAudioBlob(audioBlob) {
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);

  const handleEnded = () => {};
  const handleError = () => {};

  let playbackPromise;

  try {
    playbackPromise = new Promise((resolve, reject) => {
      audio.addEventListener("ended", resolve, { once: true });

      audio.addEventListener(
        "error",
        () => reject(audio.error ?? new Error("Audio playback failed.")),
        { once: true },
      );
    });

    await audio.play();
    await playbackPromise;
  } finally {
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
    URL.revokeObjectURL(audioUrl);
  }
}
