
import apiClient from "./client";

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
