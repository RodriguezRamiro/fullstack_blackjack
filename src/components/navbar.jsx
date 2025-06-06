// src/components/navbar.jsx

import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import '../styles/blackjackgame.css'


export default function Navbar({ tableId, playerId, socket, username }) {
    const navigate = useNavigate();
    const location = useLocation();

    const leaveTable = () => {
        if ( tableId && playerId && socket) {
            socket.emit("leave", { tableId, playerId });
        }
        navigate("/");
    };

    const isInGame = location.pathname.includes("/table/");

    return (
        <nav className="navbar">
          <div className="navbar-left">
            <Link to="/" className="navbar-logo">♠ Blackjack</Link>
          </div>

          <div className='navbar-right'>
            {username && <span className='navbar-user'>👤{username}</span>}
            {isInGame && tableId && (
                <>
                <span className='nabar-table'>🃏 Table: {tableId.slice(0,6)}...</span>
                <button onClick={leaveTable} className='navbar-button'>🚪 Leave Table</button>
                </>
            )}
          </div>
    </nav>
  );
}
