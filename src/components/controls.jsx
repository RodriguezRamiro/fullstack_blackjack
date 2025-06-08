// Controls.jsx


import React from 'react';

export default function Controls({
  onDeal,
  onHit,
  onStay,
  disabled,
  gameOver,
  canDeal
}) {
  return (
    <div className="controls">
      <button onClick={onDeal} disabled={!canDeal}>Deal</button>
      <button onClick={onHit} disabled={disabled || gameOver}>Hit</button>
      <button onClick={onStay} disabled={disabled || gameOver}>Stay</button>
    </div>
  );
}
