// src/components/PlayerSeat.jsx
import React, { useState } from 'react';
import { cardBack } from '../assets/assets';

const PlayerSeat = ({ player, isCurrent, revealHands }) => {
  const [input, setInput] = useState('');

  const shouldShowCards = isCurrent || revealHands;


  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <div className={`player-seat ${isCurrent ? 'current-turn' : ''}`}>
      <div className="player-hand-group">
        <div className="avatar">
          <span className="avatar-circle">{player.username[0].toUpperCase()}</span>
          <span className="username">{player.username}</span>
        </div>

        <div className="hand">
          {player.hand.map((card, idx) => {
            const imgSrc = shouldShowCards && card.image ? card.image : cardBack;
            return (
              <img
                key={idx}
                src={imgSrc}
                alt={shouldShowCards ? `${card.rank} of ${card.suit}` : 'Hidden card'}
                className="card-img player-card"
              />
            );
          })}
        </div>

        {player.chatBubble && <div className="chat-bubble">{player.chatBubble}</div>}
      </div>

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
