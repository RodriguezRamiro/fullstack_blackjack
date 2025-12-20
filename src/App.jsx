/* //fullstack_blackjack_vite/src/App.jsx */

import React, { useState } from 'react';
import {
  BrowserRouter as Router,
  Route,
  Routes,
  useLocation,
  useNavigate
} from 'react-router-dom';

import './App.css';
import socket from './socket';
import { BACKEND_URL } from './config';
import BlackjackGame from './components/blackjack';
import GlobalChat from './components/globalchat';
import Navbar from './components/navbar';
import UsernamePrompt from './components/usernameprompt';
import Footer from './components/footer';




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
      navigate(`/table/${data.table_id}`);
    } catch (error) {
      console.error("Error creating table:", error);
    }
  };

  const joinTable = () => {
    const inputId = prompt("Enter Table ID");
    if (inputId) {
      navigate(`/table/${inputId}`);
    }
  };

  return (
    <div className="lobby-card">
      <h1>Blackjack</h1>

      <div className="table-controls">
        <button onClick={createTable}>Create Table</button>
        <button onClick={joinTable}>Join Table</button>
      </div>
    </div>
  );
}


function useTableIdFromPath() {
  const location = useLocation();
  const match = location.pathname.match(/\/table\/([^/]+)/);
  return match ? match[1] : null;
}

function AppRoutes({ playerId, username }) {
  const tableId = useTableIdFromPath();

  return (
    <>
    <div className='lobby-background'>
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
        <GlobalChat username={username} />
      </div>
    </>
  );
}

function App() {
  const [username, setUsername] = useState(() => {
    return localStorage.getItem("username") || "";
  });

  const [playerId] = useState(() => {
    let id = localStorage.getItem("playerId");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("playerId", id);
    }
    return id;
  });

  if (!username) {
    return <UsernamePrompt onSetUsername={(name) => {
      setUsername(name);
      localStorage.setItem("username", name);
    }} />;
  }

  return (
    <Router>
      <AppRoutes playerId={playerId} username={username} />
      <Footer />
    </Router>

  );
}

export default App;
