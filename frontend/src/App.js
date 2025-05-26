import React, { useState } from 'react';
import './App.css';
import socket from './socket';
import BlackjackGame from './components/blackjack';
import GlobalChat from './components/globalchat';

function App() {
  const [tableId, setTableId] = useState(null);
  const [username] = useState("Player");
  const [playerId] = useState(() => {
    let id = localStorage.getItem("playerId");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("playerId", id);
    }
    return id;
  });

  // ✅ Make sure this function is defined BEFORE it's used
  const createTable = async () => {
    try {
      const res = await fetch("/create-room", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
      });

      const data = await res.json();
      setTableId(data.tableId);
      socket.emit("join", { tableId: data.tableId, playerId, username });
    } catch (error) {
      console.error("Error creating table:", error);
    }
  };

  const joinTable = (incomingTableId) => {
    if (!incomingTableId) return;
    setTableId(incomingTableId);
    socket.emit("join", { tableId: incomingTableId, playerId, username });
  };

  return (
    <main className="app-container">
      {tableId ? (
        <BlackjackGame
          username={username}
          playerId={playerId}
          tableId={tableId}
        />
      ) : (
        <div className="lobby-background">
          <h1>Blackjack</h1>
          <div className="table-controls">
            <button onClick={createTable}>Create Table</button>
            <button
              onClick={() => {
                const inputId = prompt("Enter Table ID");
                if (inputId) joinTable(inputId);
              }}
            >
              Join Table
            </button>
          </div>
          <GlobalChat username={username} />
        </div>
      )}
    </main>
  );
}


export default App;
