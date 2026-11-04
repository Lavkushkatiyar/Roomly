import apiClient from "./client";

function getRoomApiError(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (!error?.response) {
    return "Could not reach Roomly. Check that the backend is running and try again.";
  }

  return `Room setup failed (${error.response.status}). Please try again.`;
}

async function getRooms() {
  const response = await apiClient.get("hotel_room/");
  if (!Array.isArray(response.data)) {
    throw new Error("Roomly returned an unexpected room list.");
  }

  return response.data;
}

export async function getOrCreateRoom(roomNumber) {
  const normalizedRoomNumber = roomNumber.trim();
  if (!normalizedRoomNumber || normalizedRoomNumber.length > 10) {
    throw new TypeError("Enter a room number between 1 and 10 characters.");
  }

  try {
    let rooms = await getRooms();
    let room = rooms.find(
      (candidate) => candidate.room_number === normalizedRoomNumber,
    );

    if (!room) {
      await apiClient.post("hotel_room/", null, {
        params: { room_number: normalizedRoomNumber },
      });
      rooms = await getRooms();
      room = rooms.find(
        (candidate) => candidate.room_number === normalizedRoomNumber,
      );
    }

    if (!room || typeof room.id !== "string") {
      throw new Error("Roomly could not find the room after setup.");
    }

    if (!room.is_active) {
      throw new Error(
        "This room is not currently available. Please contact the front desk.",
      );
    }

    return room;
  } catch (error) {
    if (
      error instanceof TypeError ||
      (error instanceof Error &&
        (error.message.startsWith("Roomly ") ||
          error.message.startsWith("This room ")))
    ) {
      throw error;
    }

    throw new Error(getRoomApiError(error), { cause: error });
  }
}
