//playerhan.jsx

import React from 'react';
import playerImage from '../assets/icons8-croupier-64 (1).png';

export default function PlayerHand({ cards = [] }) {
  const calculateHandValue = (cards) => {
    let value = 0;
    let aceCount = 0;

    cards.forEach(card => {
      if (['KING', 'QUEEN', 'JACK'].includes(card.value)) {
        value += 10;
      } else if (card.value === 'ACE') {
        value += 11;
        aceCount++;
      } else {
        value += parseInt(card.value);
      }
    });

    while (value > 21 && aceCount > 0) {
      value -= 10;
      aceCount--;
    }

    return value;
  };

  return (
    <div className="player-area">
      {/* Player Avatar */}
      <div className="player-avatar">
      <img
  src={playerImage}
  alt="Player Avatar"
  className="player-avatar"
        />
      </div>
      <h2>Player's Hand</h2>

      <div className="card-row">
        {cards.length > 0 ? (
          cards.map((card, idx) => (
            <img
              key={idx}
              src={card.image}
              alt={`Card ${card.value} of ${card.suit}`}
              className="card-img"
            />
          ))
        ) : (
          <p>No cards dealt yet</p>
        )}
      </div>

      {cards.length > 0 && (
        <div className="hand-value">
          <p>Total Value: {calculateHandValue(cards)}</p>
        </div>
      )}
    </div>
  );
}
