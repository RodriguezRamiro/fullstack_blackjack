// src/components/TableSeats.jsx
import React, { useEffect } from 'react';
import PlayerSeat from './PlayerSeat';
import '../styles/blackjackgame.css';

const TableSeats = ({ players, currentPlayerId, onSendMessage, revealHands = false }) => {
  const count = players.length;

  // Debugging: detect missing or duplicate player IDs
  useEffect(() => {
    const ids = players.map(p => p.playerId);
    const missingIds = ids.filter(id => !id);
    const uniqueIds = new Set(ids);

    if (missingIds.length > 0) {
      console.warn('Some players are missing playerId:', players);
    }
    if (uniqueIds.size !== ids.length) {
      console.warn('Duplicate playerId values detected:', ids);
    }
  }, [players]);

  return (
    <div className="table-seats-container">
      {players.map((player, idx) => {
        const angle = (360 / count) * idx; // even seat spacing
        const key = player.playerId ?? `seat-fallback-${idx}`;

        return (
          <div
            key={key}
            className="seat-wrapper"
            data-angle={angle}
            style={{ '--seat-angle': `${angle}deg` }}
          >
            <PlayerSeat
              player={player}
              isCurrent={player.playerId === currentPlayerId}
              revealHands={revealHands}
              onSendMessage={onSendMessage}
            />
          </div>
        );
      })}
    </div>
  );
};

export default TableSeats;
