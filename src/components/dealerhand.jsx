// dealerhand.jsx

import React from 'react';
import dealerImage from '../assets/icons8-croupier-96 (2).png';
import { cardBack } from '../assets/assets';

export default function DealerHand({ cards = [], reveal = true }) {
  const calculateHandValue = (cards) => {
    let total = 0;
    let aceCount = 0;

    cards.forEach(card => {
      const value = card?.rank?.toUpperCase();

      if (!value) return;

      if (['K', 'Q', 'J'].includes(value)) {
        total += 10;
      } else if (value === 'A') {
        total += 11;
        aceCount += 1;
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

  const displayCards = reveal
    ? cards
    : cards.map((card, idx) =>
        idx === 0
          ? {

              ...card,
              image: cardBack,
              code: 'Hidden',
              rank: 'Hidden',
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
            alt={card.code === 'Hidden' ? 'Facedown card' : `Card ${card.rank} of ${card.suit}`}
            className="card-img"
            />
          ))
        ) : (
          <p>No cards dealt yet</p>
        )}
      </div>

      {reveal && cards.length > 0 && (
        <div className="hand-value">
          <p>Total: {calculateHandValue(cards)}</p>
        </div>
      )}
    </div>
  );
}