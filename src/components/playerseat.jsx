// src/components/PlayerSeat.jsx
import React, { useState } from 'react';
import { cardBack } from '../assets/assets';

const PlayerSeat = ({ player, isCurrent, revealHands, onSendMessage }) => {
  const [input, setInput] = useState('');

  const shouldShowCards = revealHands || isCurrent;


  const handleSend = () => {
    if (input.trim()) {
      onSendMessage?.(input.trim());
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
          <span className="avatar-circle">
            {player.username?.[0]?.toUpperCase?.() || '?'}
            </span>
          <span className="username">{player.username || 'Player'}</span>
        </div>

        <div className="hand">
          {player.hand?.length > 0 ? (
            player.hand.map((card, idx) => {
              // Determine image source
              const isHidden = !shouldShowCards;
              const imgSrc = isHidden
                ? cardBack
                : card?.image || `/cards/${card.value}_of_${card.suit}.png`;

              const altText = isHidden
                ? 'Hidden card'
                : `Card ${card.value} of ${card.suit}`;

              return (
                <img
                  key={`card-${idx}`}
                  src={imgSrc}
                  alt={altText}
                  className="card-img player-card"
                />
              );
            })
          ) : (
            <p className="no-cards">No cards yet</p>
          )}
        </div>

        {player.chatBubble && (
          <div className="chat-bubble">{player.chatBubble}</div>
        )}
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
