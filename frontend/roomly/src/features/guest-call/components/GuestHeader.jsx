export function GuestHeader({ roomNumber, onLogOut }) {
  return (
    <header className="guest-header">
      <a
        className="guest-header__brand"
        href="/"
        aria-label="Roomly Guest Concierge home"
      >
        <img className="guest-header__logo" src="/roomly-logo.png" alt="" />
      </a>

      <div className="guest-header__account">
        {roomNumber ? (
          <span className="guest-header__room">
            <span className="guest-header__room-dot" aria-hidden="true" />
            Room {roomNumber}
          </span>
        ) : (
          <span className="guest-header__descriptor">Guest access</span>
        )}
        <span className="guest-header__profile" aria-hidden="true">
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
        {roomNumber && (
          <button
            className="guest-header__logout"
            onClick={onLogOut}
            type="button"
          >
            Log out
          </button>
        )}
      </div>
    </header>
  );
}
