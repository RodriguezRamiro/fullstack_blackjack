//src/components/UsernamePrompt.jsx


import React, { useState } from 'react';


const UsernamePrompt = ({ onSetUsername }) => {
    const [input, setInput] = useState("");

    const handleSubmit = () => {
        const trimmed = input.trim();
        if (trimmed.length === 0 ) return;
        onSetUsername(trimmed);
    };

    return (
        <div className="userame-prompt">
            <h2> Enter username</h2>
            <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            handleSubmit();
          }
        }}
      />
            <button onClick={handleSubmit}>Continue</button>
        </div>
    );
};

export default UsernamePrompt;