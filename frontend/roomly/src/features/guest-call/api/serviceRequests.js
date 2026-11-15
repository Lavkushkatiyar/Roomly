
import apiClient from "./client";

export async function getServiceRequests(roomId, { signal } = {}) {
  if (!roomId) {
    throw new TypeError("A room is required to load service requests.");
  }

  try {
    const response = await apiClient.get("service-requests/", {
      params: { room_id: roomId, limit: 100 },
      signal,
    });

    if (
      !Array.isArray(response.data) ||
      response.data.some(
        (request) =>
          typeof request?.id !== "string" ||
          typeof request?.category !== "string" ||
          typeof request?.staff_summary !== "string" ||
          typeof request?.status !== "string" ||
          typeof request?.created_at !== "string",
      )
    ) {
      throw new Error("Roomly returned an unexpected service request list.");
    }

    return response.data;
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("Roomly ")) {
      throw error;
    }

    if (error?.code === "ERR_CANCELED") {
      throw error;
    }

    const detail = error?.response?.data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : error?.response
          ? `Could not load your requests (${error.response.status}). Please try again.`
          : "Could not reach Roomly to load your requests. Check your connection and try again.";
    throw new Error(message, { cause: error });
  }
}

export async function createServiceRequests(rawInputId, tasks) {
  try {
    const response = await apiClient.post("service-requests/batch", {
      raw_input_id: rawInputId,
      requests: tasks,
    });

    return response.data;
  } catch (error) {
    const detail = error?.response?.data?.detail;

    throw new Error(
      typeof detail === "string"
        ? detail
        : "Could not save the confirmed service requests.",
      { cause: error },
    );
  }
}
