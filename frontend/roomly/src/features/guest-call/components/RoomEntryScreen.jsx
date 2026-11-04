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
      <section className="room-entry__content" aria-labelledby="room-entry-title">
        <p className="room-entry__eyebrow">
          <span aria-hidden="true" />
          Your personal guest concierge
        </p>
        <h1 id="room-entry-title">Enter your room.</h1>
        <p className="room-entry__intro">
          Enter your room number and choose the language
        </p>

        <form className="room-entry__form" onSubmit={handleSubmit}>
          <label className="room-entry__field">
            <span className="room-entry__label">
              <span>Room number</span>
              <span className="room-entry__field-hint">Suite key</span>
            </span>
            <input
              autoComplete="off"
              maxLength={10}
              name="roomNumber"
              onChange={(event) => setRoomNumber(event.target.value)}
              placeholder="e.g. 402"
              required
              value={roomNumber}
            />
          </label>

          <label className="room-entry__field">
            <span className="room-entry__label">
              <span>Preferred language</span>
              <span className="room-entry__field-hint">Concierge voice</span>
            </span>
            <select
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
          </label>

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
            {isSubmitting ? "Preparing your room..." : "Enter room concierge"}
            <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
              <path
                d="M3.5 10h12m-5-5 5 5-5 5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          <p className="room-entry__help">
            <span aria-hidden="true">ⓘ</span>
            Need assistance with check-in? Please contact the front desk.
          </p>
        </form>

        <p className="room-entry__connection">
          <span aria-hidden="true">◇</span>
          Room number and language are remembered in this browser.
        </p>
      </section>

      <footer className="room-entry__footer">
        <span>Your comfort, our priority.</span>
        <span>Roomly guest concierge</span>
      </footer>
    </main>
  );
}
