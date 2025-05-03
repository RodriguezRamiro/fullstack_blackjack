// Controls.jsx


import React from 'react';

export default function Controls({
  onDeal,
  onHit,
  onStay,
  onReset,
  disabled,
  gameOver,
  canDeal
}) {
  return (
    <div className="controls">
      <button onClick={onDeal} disabled={!canDeal}>Deal</button>
      <button onClick={onHit} disabled={disabled || gameOver}>Hit</button>
      <button onClick={onStay} disabled={disabled || gameOver}>Stay</button>
      <button onClick={onReset}>Reset</button>
    </div>
  );
}
