import React from 'react';
import './App.css';
import Chatbox from './components/chatbox';
import BlackjackGame from './components/blackjack';

function App() {
  return (
    <>
      <main className="app-container">
        <BlackjackGame />
        <Chatbox />
      </main>
    </>
  );
}

export default App;
