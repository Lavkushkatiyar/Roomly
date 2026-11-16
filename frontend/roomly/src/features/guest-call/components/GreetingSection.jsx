export function GreetingSection() {
  const currentHour = new Date().getHours();

  const greeting =
    currentHour < 12
      ? "Good morning"
      : currentHour < 17
        ? "Good afternoon"
        : "Good evening";


  return (
    <header className="greeting">
      <p className="greeting__eyebrow">{greeting}</p>
      <h1 id="guest-call-title">How may we assist you?</h1>
      <p className="greeting__support">
        Speak naturally. We are here to help.
      </p>
    </header>
  );
}
