const CHIME_DURATION_MS = 500;

export async function playGreetingChime({ signal } = {}) {
  if (signal?.aborted) {
    return;
  }

  const AudioContextConstructor =
    window.AudioContext ?? window.webkitAudioContext;
  if (!AudioContextConstructor) {
    return;
  }

  const context = new AudioContextConstructor();
  const oscillators = [];
  let timer;
  let handleAbort;

  try {
    let finishPlayback;
    const playback = new Promise((resolve) => {
      finishPlayback = resolve;
      handleAbort = () => resolve();
      signal?.addEventListener("abort", handleAbort, { once: true });
    });

    if (signal?.aborted) {
      finishPlayback();
    }

    await Promise.race([context.resume(), playback]);
    if (signal?.aborted) {
      return;
    }

    const now = context.currentTime;
    const notes = [
      { frequency: 880, start: 0, volume: 0.12 },
      { frequency: 1174.66, start: 0.07, volume: 0.07 },
    ];

    for (const note of notes) {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "sine";
      oscillator.frequency.value = note.frequency;
      gain.gain.setValueAtTime(0.0001, now + note.start);
      gain.gain.exponentialRampToValueAtTime(
        note.volume,
        now + note.start + 0.025,
      );
      gain.gain.exponentialRampToValueAtTime(
        0.0001,
        now + CHIME_DURATION_MS / 1000,
      );
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start(now + note.start);
      oscillator.stop(now + CHIME_DURATION_MS / 1000);
      oscillators.push(oscillator);
    }

    timer = window.setTimeout(finishPlayback, CHIME_DURATION_MS);
    await playback;
  } finally {
    window.clearTimeout(timer);
    signal?.removeEventListener("abort", handleAbort);
    oscillators.forEach((oscillator) => oscillator.stop());
    await context.close();
  }
}
