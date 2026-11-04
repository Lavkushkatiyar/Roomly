import { useState } from "react";

import { getOrCreateRoom } from "./features/guest-call/api/hotelRooms";
import { GuestCallScreen } from "./features/guest-call/components/GuestCallScreen";
import { GuestHeader } from "./features/guest-call/components/GuestHeader";
import { RoomEntryScreen } from "./features/guest-call/components/RoomEntryScreen";
import {
  loadGuestSession,
  saveGuestSession,
} from "./features/guest-call/utils/guestSession";

export default function App() {
  const [guestSession, setGuestSession] = useState(loadGuestSession);

  const enterRoom = async ({ roomNumber, guestLanguage }) => {
    const room = await getOrCreateRoom(roomNumber);
    const session = {
      roomId: room.id,
      roomNumber: room.room_number,
      guestLanguage,
    };

    saveGuestSession(session);
    setGuestSession(session);
  };

  return (
    <>
      <GuestHeader roomNumber={guestSession?.roomNumber} />
      {guestSession ? (
        <GuestCallScreen
          guestLanguage={guestSession.guestLanguage}
          roomId={guestSession.roomId}
        />
      ) : (
        <RoomEntryScreen onEnter={enterRoom} />
      )}
    </>
  );
}
