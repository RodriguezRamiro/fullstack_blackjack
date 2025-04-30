// PlayerHand.jsx


import React from 'react';

export default function PlayerHand({ cards = [] }) {
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
    <div className="player-area">
      <h2>Player's Hand</h2>
      <div className="card-row">
        {cards.length > 0 ? (
          cards.map((card, idx) => (
            <img key={idx} src={card.image} alt={card.code} className="card-img" />
          ))
        ) : (
          <p>No cards dealt yet</p>  // Fallback message when no cards are available
        )}
      </div>

      {/* Display the total value of the player's hand */}
      {cards.length > 0 && (
        <div className="hand-value">
          <p>Total Value: {calculateHandValue(cards)}</p>
        </div>
      )}

      {/* The avatar ring now sits outside the table */}
      <div className="avatar-ring">
        {[...Array(5)].map((_, idx) => (
          <div key={idx} className={`avatar-placeholder avatar-${idx}`} />
        ))}
      </div>
    </div>
  );
}
