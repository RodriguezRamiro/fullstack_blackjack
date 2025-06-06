import React, { useState } from 'react';
import {
  BrowserRouter as Router,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom';

import './App.css';
import socket from './socket';
import { BACKEND_URL } from './config';
import { useNavigate } from 'react-router-dom';
import BlackjackGame from './components/blackjack';
import GlobalChat from './components/globalchat';
import Navbar from './components/navbar';

function Lobby({ playerId, username }) {
  const navigate = useNavigate();

  const createTable = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/create-room`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status} ${res.statusText}`);
      }

      const data = await res.json();
      navigate(`/table/${data.tableId}`);
      socket.emit("join", { tableId: data.tableId, playerId, username });
    } catch (error) {
      console.error("Error creating table:", error);
    }
  };

  const joinTable = () => {
    const inputId = prompt("Enter Table ID");
    if (inputId) {
      navigate(`/table/${inputId}`);
      socket.emit("join", { tableId: inputId, playerId, username });
    }
  };

  return (
    <div className="lobby-background">
      <h1>Blackjack</h1>
      <div className="table-controls">
        <button onClick={createTable}>Create Table</button>
        <button onClick={joinTable}>Join Table</button>
      </div>
      <GlobalChat username={username} />
    </div>
  );
}

// Hook to extract tableId from URL if present
function useTableIdFromPath() {
  const location = useLocation();
  const match = location.pathname.match(/\/table\/([^/]+)/);
  return match ? match[1] : null;
}

function AppRoutes({ playerId, username }) {
  const tableId = useTableIdFromPath();

  return (
    <>
      <Navbar
        tableId={tableId}
        playerId={playerId}
        socket={socket}
        username={username}
      />
      <main className="app-container">
        <Routes>
          <Route
            path="/"
            element={<Lobby playerId={playerId} username={username} />}
          />
          <Route
            path="/table/:tableId"
            element={<BlackjackGame playerId={playerId} username={username} />}
          />
        </Routes>
      </main>
    </>
  );
}

function App() {
  const [username] = useState("Player");
  const [playerId] = useState(() => {
    let id = localStorage.getItem("playerId");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("playerId", id);
    }
    return id;
  });

  return (
    <Router>
      <AppRoutes playerId={playerId} username={username} />
    </Router>
  );
}

export default App;
