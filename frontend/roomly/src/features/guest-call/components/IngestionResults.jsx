export function IngestionResults({ result }) {
  if (!result) {
    return null;
  }

  const tasks = result.extraction.tasks;

  return (
    <section
      className="ingestion-results"
      aria-labelledby="ingestion-results-title"
    >
      <h2 id="ingestion-results-title" className="ingestion-results__title">
        Your request
      </h2>

      <section className="ingestion-results__section">
        <h3 className="ingestion-results__label">Transcript</h3>
        <p className="ingestion-results__transcript">
          {result.raw_input.transcript}
        </p>
      </section>

      <section className="ingestion-results__section">
        <h3 className="ingestion-results__label">Proposed service tasks</h3>
        {tasks.length > 0 ? (
          <ul className="ingestion-results__tasks">
            {tasks.map((task, index) => (
              <li
                className="ingestion-results__task"
                key={`${task.category}-${index}`}
              >
                <div className="ingestion-results__task-heading">
                  <span className="ingestion-results__category">
                    {task.category.replaceAll("_", " ")}
                  </span>
                  <span className="ingestion-results__priority">
                    {task.priority}
                  </span>
                </div>
                <p>{task.staff_summary}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="ingestion-results__empty">
            No service tasks were identified.
          </p>
        )}
      </section>
    </section>
  );
}
