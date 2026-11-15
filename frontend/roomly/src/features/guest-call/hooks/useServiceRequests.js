import { useCallback, useEffect, useState } from "react";

import { getServiceRequests } from "../api/serviceRequests";

export function useServiceRequests(roomId) {
  const [requests, setRequests] = useState([]);
  const [status, setStatus] = useState("loading");
  const [errorMessage, setErrorMessage] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setStatus("loading");
    setErrorMessage(null);
    setReloadKey((current) => current + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    getServiceRequests(roomId, { signal: controller.signal })
      .then((loadedRequests) => {
        if (!controller.signal.aborted) {
          setRequests(loadedRequests);
          setStatus("loaded");
        }
      })
      .catch((error) => {
        if (controller.signal.aborted) {
          return;
        }

        setStatus("error");
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Could not load your requests. Please try again.",
        );
      });

    return () => controller.abort();
  }, [reloadKey, roomId]);

  return { requests, status, errorMessage, reload };
}
