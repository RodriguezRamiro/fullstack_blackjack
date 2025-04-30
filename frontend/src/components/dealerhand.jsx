// DealerHand.jsx
import React from 'react';

export default function DealerHand({ cards = [] }) {
  // Function to calculate the total hand value
  const calculateHandValue = (cards) => {
    let value = 0;
    let aceCount = 0;

    cards.forEach(card => {
      if (card.value === 'KING' || card.value === 'QUEEN' || card.value === 'JACK') {
        value += 10;
      } else if (card.value === 'ACE') {
        value += 11;
        aceCount += 1;
      } else {
        value += parseInt(card.value);
      }
    });

    // Adjust for aces if the value exceeds 21
    while (value > 21 && aceCount > 0) {
      value -= 10;
      aceCount -= 1;
    }

    return value;
  };

  return (
    <div className="dealer-area">
      {/* Conditional rendering of the avatar */}
      <div className="dealer-avatar" />
      <h2>Dealer's Hand</h2>
      <div className="card-row">
        {Array.isArray(cards) && cards.length > 0 ? (
          cards.map((card, idx) => (
            <img key={idx} src={card.image} alt={card.code} className="card-img" />
          ))
        ) : (
          <p>No cards dealt yet</p>  // Fallback text if no cards are available
        )}
      </div>
      {/* Display the total value of the dealer's hand */}
      {cards.length > 0 && (
        <div className="hand-value">
          <p>Total Value: {calculateHandValue(cards)}</p>
        </div>
      )}
    </div>
  );
}
