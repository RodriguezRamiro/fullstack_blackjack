// src/components/PlayerSeat.jsx
import React, { useState } from 'react';
import { cardBack } from '../assets/assets';

const PlayerSeat = ({
  player,
  players,
  isCurrent,
  currentPlayerId,
  onSendMessage,
  revealHands
}) => {
  const [input, setInput] = useState('');

  if (!player) return null;

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSend();
  };

  const renderHand = (p) => {
    const shouldReveal = p.playerId === currentPlayerId || revealHands;
    return (
      <div className="hand">
        {p.hand.map((card, idx) => (
          <img
            key={idx}
            src={shouldReveal ? card.image || cardBack : cardBack}
            alt={
              shouldReveal
                ? `${card.rank || 'Hidden'} of ${card.suit || 'Hidden'}`
                : 'Hidden card'
            }
            className="card-img player-card"
          />
        ))}
      </div>
    );
  };

  const renderPlayer = (p) => (
    <div key={p.playerId} className="player-hand-group">
      <div className="avatar">
        <span className="avatar-circle">{p.username[0].toUpperCase()}</span>
        <span className="username">{p.username}</span>
      </div>
      {renderHand(p)}
      {p.chatBubble && <div className="chat-bubble">{p.chatBubble}</div>}
    </div>
  );

  return (
    <div className={`player-seat ${isCurrent ? 'current-turn' : ''}`}>
      {Array.isArray(players) && players.length > 0
        ? players.map(renderPlayer) // Multi-player mode
        : renderPlayer(player) // Single-player mode
      }

      {/* Optional Chat Input for Current Player */}
      {isCurrent && (
        <div className="chat-input">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
          />
          <button onClick={handleSend}>Send</button>
        </div>
      )}
    </div>
  );
};

export default PlayerSeat;
