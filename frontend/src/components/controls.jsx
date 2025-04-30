// Controls.jsx
import React from 'react';

export default function Controls({ onDeal, onHit, onStay, onReset, disabled, gameOver }) {
  return (
    <div className="controls">
      <button onClick={() => { console.log("Deal clicked"); onDeal(); }} disabled={!gameOver && disabled}>Deal</button>
<button onClick={() => { console.log("Hit clicked"); onHit(); }} disabled={disabled || gameOver}>Hit</button>
<button onClick={() => { console.log("Stay clicked"); onStay(); }} disabled={disabled || gameOver}>Stay</button>
<button onClick={() => { console.log("Reset clicked"); onReset(); }}>Reset</button>

    </div>
  );
}
