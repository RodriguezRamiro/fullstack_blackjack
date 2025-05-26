// blackjack.jsx

import React, { useEffect, useState } from 'react';
import socket from '../socket';
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';
import RoomChat from './roomchat';

export default function BlackjackGame({ playerId, username, tableId }) {
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to backend via Socket.IO');
    });

    socket.on('game_state', (state) => {
      const player = state.players[playerId];
      setPlayerCards(player ? player.hand : []);
      setDealerCards(state.dealer.hand);
      setPlayerTurn(player ? player.status === 'playing' : false);
      setGameOver(state.game_over);
    });

    return () => {
      socket.off('connect');
      socket.off('game_state');
    };
  }, [playerId]);

  useEffect(() => {
    if (!tableId) return;

    socket.on('joined_room', ({ tableId }) => {
      const playerId = localStorage.getItem('playerId');
      const message = 'Hello from Player!';

      socket.emit('chat_message', {
        tableId,
        playerId,
        message,
        username,
      });

      console.log(`Successfully joined room: ${tableId}`);
    });

    return () => {
      socket.off('joined_room');
    };
  }, [tableId, username]);

  const startGame = async () => {
    if (!tableId || !playerId) {
      console.error('Missing tableId or playerId');
      return;
    }

    try {
      const response = await fetch('http://localhost:5001/start-game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tableId, playerId }),
        credentials: 'include',
      });

      const data = await response.json();
      console.log('Game started at table:', data.tableId);
    } catch (error) {
      console.error('Error starting the game:', error);
    }
  };

  const hit = () => {
    socket.emit('hit', { tableId, playerId });
  };

  const stay = () => {
    socket.emit('stay', { tableId, playerId });
  };

  const renderResult = () => gameOver ? 'Game over. Check results!' : null;

  return (
    <div className="game-wrapper">
      {tableId ? (
        <div className="blackjack-table">
          <h1>Blackjack</h1>
          <p><strong>Table ID:</strong> {tableId}</p>
          <button
            className="copy-button"
            onClick={() => navigator.clipboard.writeText(tableId)}
            title="Copy Table ID"
          >
            📋
          </button>

          <DealerHand cards={dealerCards} />
          <PlayerHand cards={playerCards} />
          <Controls
            onDeal={startGame}
            onHit={hit}
            onStay={stay}
            onReset={() => window.location.reload()}
            disabled={!playerTurn}
            gameOver={gameOver}
            canDeal={true}
          />

          {gameOver && (
            <div className="game-over-message">
              <strong>{renderResult()}</strong>
            </div>
          )}
        </div>
      ) : (
        <p style={{ textAlign: 'center' }}>Waiting to join a table...</p>
      )}
      {/* Add ChatBox here */}
      <RoomChat
  socket={socket}
  tableId={tableId}
  playerId={playerId}
  username={username}
/>
    </div>
  );
}
