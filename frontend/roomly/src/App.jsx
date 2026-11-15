import { useState } from "react";

import { getOrCreateRoom } from "./features/guest-call/api/hotelRooms";
import { GuestCallScreen } from "./features/guest-call/components/GuestCallScreen";
import { GuestHeader } from "./features/guest-call/components/GuestHeader";
import { RoomEntryScreen } from "./features/guest-call/components/RoomEntryScreen";
import {
  clearGuestSession,
  loadGuestSession,
  saveGuestSession,
} from "./features/guest-call/utils/guestSession";

export default function App() {
  const [guestSession, setGuestSession] = useState(loadGuestSession);
  const [isGuideOpen, setIsGuideOpen] = useState(false);

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

  const logOut = () => {
    clearGuestSession();
    setGuestSession(null);
    setIsGuideOpen(false);
  };

  return (
    <>
      <GuestHeader
        onOpenGuide={() => setIsGuideOpen(true)}
        onLogOut={logOut}
        roomNumber={guestSession?.roomNumber}
      />
      {guestSession ? (
        <GuestCallScreen
          guestLanguage={guestSession.guestLanguage}
          isGuideOpen={isGuideOpen}
          onGuideClose={() => setIsGuideOpen(false)}
          roomId={guestSession.roomId}
        />
      ) : (
        <RoomEntryScreen onEnter={enterRoom} />
      )}
    </>
  );
}
