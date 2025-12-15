// src/components/PlayerSeat.jsx
import React, { useState } from 'react';
import cardBack from '../assets/cardBack.png';

export default function PlayerSeat({ player, isCurrent, revealHands, onSendMessage, seatIndex })
 {
   const shouldShowCards = isCurrent || revealHands;

  return (
    <div className={`player-seat ${isCurrent ? 'current-player' : ''}`}>
      <div className="player-name">
        {player.username}
        {isCurrent && ' (You)'}
      </div>

      <div className="player-cards">
        {player.hand && player.hand.length > 0 ? (
          player.hand.map((card, idx) => {
            const src = shouldShowCards && card.image
              ? card.image
              : cardBack;

              return (
              <img
                key={`${player.playerId}-${idx}`}
                src={src}
                alt="card"
                className="card-img"
              />
            );
          })
        ) : (
          <span className="no-cards">No cards</span>
        )}
      </div>

      <div className="player-score">
        {shouldShowCards ? `Score: ${player.score}` : 'Score: ?'}
      </div>
    </div>
  );
}