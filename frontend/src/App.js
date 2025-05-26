import React, { useState } from 'react';
import './App.css';
import socket from './socket';
import GlobalChat from './components/globalchat';
import BlackjackGame from './components/blackjack';
import RoomChat from './components/roomchat';

function App() {
  const [hasJoinedRoom, setHasJoinedRoom] = useState(false);
  const handleJoinRoom = (tableId) => {
    setHasJoinedRoom(true);
    setTableId(tableId);
  };

  const [username] = useState("Player"); // Hardcoded, or fetch from user input/login
  const [tableId, setTableId] = useState(null);
  const [playerId] = useState(() => {
    let id = localStorage.getItem("playerId");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("playerId", id);
    }
    return id;
  });

  console.log('App render - tableId:', tableId, 'hasJoinedRoom:', hasJoinedRoom);

  return (
    <main className="app-container">
      <BlackjackGame
        username={username}
        playerId={playerId}
        onJoinRoom={handleJoinRoom}
      />

{!hasJoinedRoom ? (
<GlobalChat username={username} />
      ) : (
        <RoomChat
          socket={socket}
          username={username}
          tableId={tableId}
          playerId={playerId}
        />
      )}
    </main>
  );
}

export default App;
