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
  ...playerList.filter(p => p.playerId !== currentPlayerId),
  ...playerList.filter(p => p.playerId === currentPlayerId),
];

  const count = sorted.length;

  // Debugging: detect missing or duplicate player IDs
  useEffect(() => {
    const ids = sorted.map(p => p.playerId);
    const missingIds = ids.filter(id => !id);
    const uniqueIds = new Set(ids);

    if (missingIds.length > 0)
    console.warn('Missing playerId:', sorted);
    if (uniqueIds.size !== ids.length)
    console.warn('Duplicate playerId:', ids);
  }, [sorted]);


  return (
    <div className="blackjack-right">
      <div className="table-seats-container">
        <div className="table-seats">
          {sorted.map((p, idx) => {
            const angle = (360 / count) * idx;
            return (
              <div
                key={p.playerId ?? `seat-${idx}`}
                className="seat-wrapper"
                data-angle={angle}
                style={{ '--seat-angle': `${angle}deg` }}
              >
                <PlayerSeat
                  player={p}
                  isCurrent={p.playerId === currentPlayerId}
                  revealHands={revealHands}
                  onSendMessage={onSendMessage}
                  seatIndex={idx}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
