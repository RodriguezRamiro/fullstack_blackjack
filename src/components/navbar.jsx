import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import '../styles/blackjackgame.css';
import Modal from './Modal';

export default function Navbar({ tableId, playerId, socket, username }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [modalOpen, setModalOpen] = useState(false);

  const leaveTable = () => {
    if (tableId && playerId && socket) {
      socket.emit("leave", { tableId, playerId });
    }
    navigate("/");
  };

  const openModal = () => setModalOpen(true);
  const closeModal = () => setModalOpen(false);

  const confirmChangeUsername = () => {
    localStorage.removeItem("username");
    window.location.reload();
  };

  const isInGame = location.pathname.includes("/table/");

  const copyTableId = () => {
    if (tableId) {
      navigator.clipboard.writeText(tableId);
      alert(`Table ID copied to clipboard: ${tableId}`);
    }
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-left">
          <Link to="/" className="navbar-logo">♠ Blackjack</Link>
        </div>

        <div className="navbar-right">
          {username && (
            <>
              <span className="navbar-user">👤 {username}</span>
              <button
                onClick={openModal}
                className="navbar-button"
              >
                Change Username
              </button>
            </>
          )}
          {isInGame && tableId && (
            <>
              <span
                className="navbar-table"
                style={{ marginLeft: '12px' }}
              >
                🃏 Table: {tableId.slice(0, 6)}...
              </span>
              <button
                onClick={copyTableId}
                className="navbar-button"
                title="Copy Full Table ID"
              >
                📋 Table Id
              </button>
              <button
                onClick={leaveTable}
                className="navbar-button"
                style={{ marginLeft: '12px' }}
              >
                🚪 Leave Table
              </button>
            </>
          )}
        </div>
      </nav>

      <Modal
        isOpen={modalOpen}
        title="Change Username?"
        message="Are you sure you want to change your username? This will clear your current username."
        onConfirm={() => {
          confirmChangeUsername();
          closeModal();
        }}
        onCancel={closeModal}
      />
    </>
  );
}
