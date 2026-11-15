import { useState } from "react";

import { GUEST_LANGUAGES } from "../utils/guestSession";
import "./room-entry.css";

export function RoomEntryScreen({ onEnter }) {
  const [roomNumber, setRoomNumber] = useState("");
  const [guestLanguage, setGuestLanguage] = useState("en-IN");
  const [errorMessage, setErrorMessage] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await onEnter({ roomNumber: roomNumber.trim(), guestLanguage });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Room setup failed. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="room-entry">
      <section
        className="room-entry__content"
        aria-labelledby="room-entry-title"
      >
        <div className="room-entry__glow" aria-hidden="true" />
        <div className="room-entry__panel">
          <p className="room-entry__eyebrow">
            <span aria-hidden="true" />
            Bespoke Guest Sanctuary
          </p>
          <h1 id="room-entry-title">Enter your room.</h1>
          <p className="room-entry__intro">
            Please enter your assigned suite key to awaken your personal in-room
            concierge.
          </p>

          <div className="room-entry__card">
            <form className="room-entry__form" onSubmit={handleSubmit}>
              <div className="room-entry__field">
                <label className="room-entry__label" htmlFor="room-number">
                  <span>Suite Number</span>
                  <span className="room-entry__field-hint">Digit Key</span>
                </label>
                <div className="room-entry__control">
                  <input
                    autoComplete="off"
                    id="room-number"
                    maxLength={10}
                    name="roomNumber"
                    onChange={(event) => setRoomNumber(event.target.value)}
                    placeholder="e.g. 402"
                    required
                    value={roomNumber}
                  />
                  <svg
                    aria-hidden="true"
                    className="room-entry__field-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <path
                      d="M5 21V4h14v17M9 21v-5h6v5M9 8h.01M15 8h.01"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              </div>

              <div className="room-entry__field">
                <label
                  className="room-entry__label"
                  htmlFor="preferred-language"
                >
                  <span>Preferred Language</span>
                  <span className="room-entry__field-hint">
                    Concierge Voice
                  </span>
                </label>
                <div className="room-entry__control">
                  <select
                    id="preferred-language"
                    name="guestLanguage"
                    onChange={(event) => setGuestLanguage(event.target.value)}
                    value={guestLanguage}
                  >
                    {GUEST_LANGUAGES.map((language) => (
                      <option key={language.value} value={language.value}>
                        {language.label}
                      </option>
                    ))}
                  </select>
                  <svg
                    aria-hidden="true"
                    className="room-entry__field-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="9"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    />
                    <path
                      d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              </div>

              {errorMessage && (
                <p className="room-entry__error" role="alert">
                  {errorMessage}
                </p>
              )}

              <button
                className="room-entry__submit"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting ? (
                  <>
                    <span className="room-entry__spinner" aria-hidden="true" />
                    Calibrating Audio Unit
                  </>
                ) : (
                  <>
                    Enter Room Concierge
                    <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
                      <path
                        d="M3.5 10h12m-5-5 5 5-5 5"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </>
                )}
              </button>
            </form>

            <p className="room-entry__help">
              <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
                <circle
                  cx="10"
                  cy="10"
                  r="7.25"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <path
                  d="M8.2 7.5a1.9 1.9 0 1 1 3.4 1.15c-.8.95-1.6 1.1-1.6 2.35M10 13.9v.1"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Need assistance with check-in? Please contact the front desk.
            </p>
          </div>

          <p className="room-entry__connection">
            <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
              <path
                d="M10 2.5 16 5v4.3c0 3.5-2.45 6.7-6 8.2-3.55-1.5-6-4.7-6-8.2V5l6-2.5Z"
                stroke="currentColor"
                strokeWidth="1.35"
                strokeLinejoin="round"
              />
              <path
                d="m7.4 9.9 1.7 1.7 3.6-3.8"
                stroke="currentColor"
                strokeWidth="1.35"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Encrypted Connection to Your Suite
          </p>
        </div>
      </section>

      <footer className="room-entry__footer">
        <span>Your comfort, our priority.</span>
        <span>Roomly guest concierge</span>
      </footer>
    </main>
  );
}
