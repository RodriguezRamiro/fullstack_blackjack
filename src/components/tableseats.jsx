// src/components/TableSeats.jsx

import React from 'react';
import PlayerSeat from './playerseat';
import '../styles/blackjackgame.css';

const TableSeats = ({ players, currentPlayerId }) => {
  const count = players.length;

  return (
    <div className="table-seats-container">
      {players.map((player, idx) => {
        const angle = (360 / count) * idx;

        return (
          <div
            key={player.playerId}
            className="seat-wrapper"
            data-angle={angle} // optional: could use in CSS or debugging
            style={{ '--seat-angle': `${angle}deg` }} // for CSS variable use
          >
            <PlayerSeat
              player={player}
              isCurrent={player.playerId === currentPlayerId}
            />
          </div>
        );
      })}
    </div>
  );
};

export default TableSeats;
