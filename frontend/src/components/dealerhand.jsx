import React from 'react';

export default function DealerHand({ cards = [], reveal = true }) {
  // Helper to calculate the hand's total value
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
        value += parseInt(card.value);
      }
    });

    while (value > 21 && aceCount > 0) {
      value -= 10;
      aceCount--;
    }

    return value;
  };

  // Optionally hide the first dealer card
  const displayCards = reveal
    ? cards
    : cards.map((card, idx) =>
        idx === 0
          ? { image: '/card-back.png', code: 'Hidden' } // placeholder back image
          : card
      );

  return (
    <div className="dealer-area">
      <div className="dealer-avatar" />
      <h2>Dealer's Hand</h2>
      <div className="card-row">
        {displayCards.length > 0 ? (
          displayCards.map((card, idx) => (
            <img
              key={idx}
              src={card.image}
              alt={card.code === 'Hidden' ? 'Hidden card' : card.code}
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
