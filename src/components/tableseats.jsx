// src/components/TableSeats.jsx


import React, { useEffect, useMemo } from 'react';
import PlayerSeat from './PlayerSeat';
import '../styles/blackjackgame.css';


/**TableSeats - visually arranges all players around the table.
 * @param {object[]} players - list of player object from backend {playerId, username, hand, ...
 * #param {string} currentPlayerId - Id of the current player
 * @param {boolean} revealHands - weather to reveal all player hands
 * @param {function} onSendMessage - callback for chat messages
 */

export default function TableSeats({ players = [], currentPlayerId, revealHands, onSendMessage }) {
  if (!players.length) {
    return <div className='table-seats-empty'>Waiting for players...</div>;
  }


  //Convert players object -> array with playerId included
  const playerList = useMemo(() => {
    if (Array.isArray(players)) return players;    // fallback for backend fail
    return Object.entries(players).map(([playerId, info]) => ({
      playerId,
      ...info
    }));
  }, [players]);

  // Sort the current player is always las (bottom of table)
  const sorted = [
  ...players.filter(p => p.playerId !== currentPlayerId),
  ...players.filter(p => p.playerId === currentPlayerId),
];

  const count = players.length;

  // Debugging: detect missing or duplicate player IDs
  useEffect(() => {
    const ids = players.map(p => p.playerId);
    const missingIds = ids.filter(id => !id);
    const uniqueIds = new Set(ids);

    if (missingIds.length > 0) {
      console.warn('Some players are missing playerId:', playerList);
    }
    if (uniqueIds.size !== ids.length) {
      console.warn('Duplicate playerId values detected:', ids);
    }
  }, [playerList, sorted]);

  return (
    <div className="table-seats-container">
      <div className="table-seats">
        {sorted.map((p, idx) => (
          <div
            key={p.playerId ?? `seat-${idx}`}
            className="seat-wrapper"
            data-angle={(360 / count) * idx}
            style={{ '--seat-angle': `${(360 / count) * idx}deg` }}
          >
            <PlayerSeat
              player={p}
              isCurrent={p.playerId === currentPlayerId}
              revealHands={revealHands}
              onSendMessage={onSendMessage}
              seatIndex={idx}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
