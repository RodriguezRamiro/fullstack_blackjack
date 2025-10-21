// src/dealerhand.jsx

import React from 'react';
import dealerImage from '../assets/icons8-croupier-96 (2).png';
import { cardBack } from '../assets/assets';

export default function DealerHand({ cards = [], reveal = true }) {
  const calculateHandValue = (cards) => {
    let total = 0;
    let aceCount = 0;

    cards.forEach(card => {
      const value = card?.value?.toUpperCase?.();
      if (!value) return;

      if (['K', 'Q', 'J'].includes(value)) total += 10;
       else if (value === 'A') {
        total += 11;
        aceCount++;
      } else if (!isNaN(value)) total += parseInt(value, 10);
    });

    while (total > 21 && aceCount > 0) {
      total -= 10;
      aceCount--;
    }

    return total;
  };

  return (
    <div className="dealer-area">
      <img
      src={dealerImage}
      alt="Dealer Avatar"
      className="dealer-avatar"
      />
      <h2>Dealer's Hand</h2>

      <div className="card-row">
        {cards.length > 0 ? (
          cards.map((card, idx) => {
            // Determine if card should be hidden
            const isHidden =
              (!reveal && idx === 1) || // hide dealer’s 2nd card when reveal = false
              card?.value === "hidden" ||
              card?.suit === "hidden";

            // Pick image source
            const imgSrc = isHidden
              ? cardBack
              : card?.image || `/cards/${card.value}_of_${card.suit}.png`;

              const altText = isHidden
              ? "Facedown card"
              : `Card ${card.value} of ${card.suit}`;

            return (
              <img
                key={`dealer-${idx}`}
                src={imgSrc}
                alt={altText}
                className='card-img'
                />
            );
          })
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