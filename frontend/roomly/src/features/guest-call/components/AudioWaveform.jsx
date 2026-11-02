const WAVEFORM_HEIGHTS = [
  8, 12, 18, 11, 24, 15, 30, 20, 12, 25, 34, 18, 27, 38, 22, 14, 30, 20, 36,
  24, 13, 28, 17, 33, 21, 12, 25, 16, 9,
];

export function AudioWaveform({ active }) {
  return (
    <div
      className={`audio-waveform${active ? " audio-waveform--active" : ""}`}
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
