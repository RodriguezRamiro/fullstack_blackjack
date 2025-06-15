import React, { useState } from 'react';

const PlayerSeat = ({ player, isCurrent, onSendMessage }) => {
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

  return (
    <div className={`player-seat ${isCurrent ? 'current-turn' : ''}`}>
      <div className="avatar">
        <span className="avatar-circle">{player.username[0].toUpperCase()}</span>
        <span className="username">{player.username}</span>
      </div>
      <div className="hand">
        {player.hand.map((card, idx) => (
          <img key={idx} src={card.image} alt={`${card.rank} of ${card.suit}`} />
        ))}
      </div>
      {player.chatBubble && (
        <div className="chat-bubble">{player.chatBubble}</div>
      )}

      {/* Only show chat input for current player (or if you want, for self) */}
      {isCurrent && (
        <div className="seat-chat-input">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Say something..."
          />
          <button onClick={handleSend}>Send</button>
        </div>
      )}
    </div>
  );
};

export default PlayerSeat;
