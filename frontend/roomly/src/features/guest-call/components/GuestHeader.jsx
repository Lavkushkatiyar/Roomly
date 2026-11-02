const roomNumber = import.meta.env.VITE_ROOM_NUMBER?.trim() || "204";

export function GuestHeader() {
  return (
    <header className="guest-header">
      <a className="guest-header__brand" href="/" aria-label="Roomly home">
        <svg
          aria-hidden="true"
          className="guest-header__logo"
          viewBox="0 0 28 28"
          fill="none"
        >
          <path
            d="M5 23V12.5L14 5l9 7.5V23h-6v-7h-6v7H5Z"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinejoin="round"
          />
          <path
            d="M11 23v-7h6v7"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
        </svg>
        <span className="guest-header__name">Roomly</span>
      </a>

      <span className="guest-header__divider" aria-hidden="true" />
      <span className="guest-header__descriptor">Guest Concierge</span>

      <div className="guest-header__account">
        <span className="guest-header__room">
          <span className="guest-header__room-dot" aria-hidden="true" />
          Room {roomNumber}
        </span>
        <span className="guest-header__profile" role="img" aria-label="Guest profile">
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none">
            <circle
              cx="12"
              cy="8"
              r="3.25"
              stroke="currentColor"
              strokeWidth="1.4"
            />
            <path
              d="M5.5 20a6.5 6.5 0 0 1 13 0"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinecap="round"
            />
          </svg>
        </span>
      </div>
    </header>
  );
}
