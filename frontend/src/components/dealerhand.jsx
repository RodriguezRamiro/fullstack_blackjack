// dealerhand.jsx

import React from 'react';
import dealerImage from '../assets/icons8-croupier-96 (2).png';

export default function DealerHand({ cards = [], reveal = true }) {
  const calculateHandValue = (cards) => {
    let value = 0;
    let aceCount = 0;

    cards.forEach(card => {
      if (['KING', 'QUEEN', 'JACK'].includes(card.value)) {
        value += 10;
      } else if (card.value === 'ACE') {
        value += 11;
        aceCount += 1;
      } else {
        value += parseInt(card.value, 10);
      }
    });

    while (value > 21 && aceCount > 0) {
      value -= 10;
      aceCount--;
    }

    return value;
  };

  const displayCards = reveal
    ? cards
    : cards.map((card, idx) =>
        idx === 0
          ? {
              image: '/card-back.png',
              code: 'Hidden',
              value: 'Hidden',
            }
          : card
      );

  return (
    <div className="dealer-area">
      <img
  src={dealerImage}
  alt="Dealer Avatar"
  className="dealer-avatar"
/>
      <h2>Dealer's Hand</h2>

      <div className="card-row">
        {displayCards.length > 0 ? (
          displayCards.map((card, idx) => (
            <img
            key={card.code !== 'Hidden' ? `${card.code}-${idx}` : `hidden-${idx}`}
            src={card.image}
            alt={card.code === 'Hidden' ? 'Facedown card' : `Card ${card.code}`}
            className="card-img"
            />
          ))
        ) : (
          <p>No cards dealt yet</p>
        )}
      </div>

      {reveal && cards.length > 0 && (
        <div className="hand-value">
          <p>Total Value: {calculateHandValue(cards)}</p>
        </div>
      )}
    </div>
  );
}