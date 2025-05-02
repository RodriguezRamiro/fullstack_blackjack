// Controls.jsx

import React from 'react';

export default function Controls({ onDeal, onHit, onStay, onReset, disabled, gameOver }) {
  return (
    <div className="controls">
      {/* Deal should be available at the start or after game over */}
      <button onClick={onDeal} disabled={playerTurn || !deckId}>Deal</button>

      <button onClick={onHit} disabled={disabled || gameOver}>
        Hit
      </button>

      <button onClick={onStay} disabled={disabled || gameOver}>
        Stay
      </button>

      <button onClick={onReset}>
        Reset
      </button>
    </div>
  );
}
