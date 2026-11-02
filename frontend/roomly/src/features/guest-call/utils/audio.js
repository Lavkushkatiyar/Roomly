const SUPPORTED_AUDIO_TYPES = [
  "audio/webm;codecs=opus",
  "audio/mp4",
  "audio/webm",
  "audio/ogg;codecs=opus",
];

export function getSupportedAudioMimeType() {
  if (typeof MediaRecorder.isTypeSupported !== "function") {
    return null;
  }

  return (
    SUPPORTED_AUDIO_TYPES.find((mimeType) =>
      MediaRecorder.isTypeSupported(mimeType),
    ) ?? null
  );
}

export async function convertAudioToWav(audioBlob) {
  const AudioContextConstructor =
    window.AudioContext ?? window.webkitAudioContext;

  if (!AudioContextConstructor) {
    throw new Error("Audio conversion is not supported by this browser.");
  }

  const audioContext = new AudioContextConstructor();

  try {
    const audioBuffer = await audioContext.decodeAudioData(
      await audioBlob.arrayBuffer(),
    );
    const channelCount = audioBuffer.numberOfChannels;
    const bytesPerSample = 2;
    const dataSize = audioBuffer.length * channelCount * bytesPerSample;
    const wavBuffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(wavBuffer);

    writeAscii(view, 0, "RIFF");
    view.setUint32(4, 36 + dataSize, true);
    writeAscii(view, 8, "WAVE");
    writeAscii(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, channelCount, true);
    view.setUint32(24, audioBuffer.sampleRate, true);
    view.setUint32(28, audioBuffer.sampleRate * channelCount * bytesPerSample, true);
    view.setUint16(32, channelCount * bytesPerSample, true);
    view.setUint16(34, bytesPerSample * 8, true);
    writeAscii(view, 36, "data");
    view.setUint32(40, dataSize, true);

    const channels = Array.from({ length: channelCount }, (_, channel) =>
      audioBuffer.getChannelData(channel),
    );
    let offset = 44;

    for (let frame = 0; frame < audioBuffer.length; frame += 1) {
      for (let channel = 0; channel < channelCount; channel += 1) {
        const sample = Math.max(-1, Math.min(1, channels[channel][frame]));
        const pcmSample = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
        view.setInt16(offset, pcmSample, true);
        offset += bytesPerSample;
      }
    }

    return new Blob([wavBuffer], { type: "audio/wav" });
  } catch {
    throw new Error("The recording could not be converted to WAV. Please try again.");
  } finally {
    await audioContext.close();
  }
}

function writeAscii(view, offset, value) {
  for (let index = 0; index < value.length; index += 1) {
    view.setUint8(offset + index, value.charCodeAt(index));
  }
}

export function stopMediaStream(stream) {
  stream?.getTracks().forEach((track) => track.stop());
}

export function getRecordingErrorMessage(error) {
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
