import React from 'react';
import playerImage from '../assets/icons8-croupier-64 (1).png';

export default function PlayerHand({ cards = [], username = "Player" }) {

  const calculateHandValue = (cards) => {
    let total = 0;
    let aceCount = 0;

    cards.forEach((card) => {
      const value = card?.rank?.toUpperCase();
      if (!value) return;

      if (['K', 'Q', 'J'].includes(value)) {
        total += 10;
      } else if (value === 'A') {
        total += 11;
        aceCount++;
      } else if (!isNaN(value)) {
        total += parseInt(value, 10);
      }
    });

    while (total > 21 && aceCount > 0) {
      total -= 10;
      aceCount--;
    }

    return total;
  };

  return (
    <div className="player-area">
      <div className="player-avatar-name">
        <img
          src={playerImage}
          alt={`${username}'s avatar`}
          className="player-hand-avatar"
        />
        <h2>{username}'s Hand</h2>
      </div>

      <div className="card-row">
        {cards.length > 0 ? (
          cards.map((card, idx) => (
            <img
              key={card.code ? `${card.code}-${idx}` : `card-${idx}`}
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
          <p>Total: {calculateHandValue(cards)}</p>
        </div>
      )}
    </div>
  );
}
