import { AudioWaveform } from "./AudioWaveform";
import { CallStatus } from "./CallStatus";
import { GreetingSection } from "./GreetingSection";
import { VoiceControl } from "./VoiceControl";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import "./guest-call.css";

export function GuestCallScreen() {
  const {
    status,
    errorMessage,
    startRecording,
    stopRecording,
  } = useAudioRecorder();

  const toggleRecording = () => {
    if (status === "recording") {
      stopRecording();
      return;
    }

    void startRecording();
  };

  return (
    <main className="guest-call" aria-labelledby="guest-call-title">
      <div className="guest-call__content">
        <GreetingSection />
        <section className="guest-call__interaction" aria-label="Voice call">
          <VoiceControl status={status} onToggle={toggleRecording} />
          <AudioWaveform active={status === "recording"} />
          <CallStatus status={status} errorMessage={errorMessage} />
        </section>
      </div>
    </main>
  );
}
