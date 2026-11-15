const WAVEFORM_HEIGHTS = [
  8, 12, 16, 24, 12, 20, 8, 16, 8,
];

export function AudioWaveform({ active, processing = false }) {
  return (
    <div
      className={`audio-waveform${active ? " audio-waveform--active" : ""}${processing ? " audio-waveform--processing" : ""}`}
      aria-hidden="true"
    >
      {WAVEFORM_HEIGHTS.map((height, index) => (
        <span
          className="audio-waveform__bar"
          key={`${height}-${index}`}
          style={{ height }}
        />
      ))}
    </div>
  );
}
