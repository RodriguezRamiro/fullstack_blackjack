// blackjack.jsx

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useNavigate } from "react-router-dom";
import { BACKEND_URL } from '../config';
import socket from '../socket';
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';
import RoomChat from './roomchat';


export default function BlackjackGame({ playerId, username }) {
  const { tableId } = useParams();
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [gameState, setGameState] = useState(null);
  const navigate = useNavigate();


  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to backend via Socket.IO');
    });

    socket.on('connect_error', (err) => {
      console.error('Socket connection error:', err);
    });

    socket.on('disconnect', () => {
      console.warn('Socket disconnected');
    });

    socket.on('room_not_found', () => {
      alert("Room does not exist.");
      navigate("/");
    });

    socket.on('game_state', (state) => {
      setGameState(state);
      const player = state?.players?.[playerId];
      setPlayerCards(player ? player.hand : []);
      setDealerCards(state.dealer?.hand || []);
      setPlayerTurn(player?.status === 'playing');
      setGameOver(state.game_over);
    });

    return () => {
      socket.off('connect');
      socket.off('connect_error');
      socket.off('disconnect');
      socket.off('game_state');
    };
  }, [playerId]);

  // Emit "join" evemt on mount or when ids change
  useEffect(() => {
    if (!tableId || !playerId || !username) return;

    socket.emit("join", { tableId, playerId, username });
    console.log(`Emitted join for player ${username} to room ${tableId}`);
  }, [tableId, playerId, username]);


  useEffect(() => {
    if (!tableId) return;

    socket.on('joined_room', ({ tableId }) => {
      const storedPlayerId = localStorage.getItem('playerId') || playerId;
      const message = 'Hello from Player!';

      socket.emit('chat_message', {
        tableId,
        playerId : storedPlayerId,
        message,
        username,
      });

      console.log(`Successfully joined room: ${tableId}`);
    });

    return () => {
      socket.off('joined_room');
    };
  }, [tableId, username, playerId]);

  const startGame = async () => {
    if (!tableId || !playerId) {
      console.error('Missing tableId or playerId');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/start-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tableId, playerId }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }

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

  const leaveTable = () => {
    socket.emit("leave", { tableId, playerId });
    navigate("/");
  };


  const renderResult = () => {
    if (!gameOver) return null;

    if (!gameState || !gameState.players) return "Game over. Check results!";

    const player = gameState.players[playerId];
    if (!player || !player.result) return "Game over. Check results!";

    switch (player.result) {
      case "win": return "You won! 🎉";
      case "lose": return "You lost. 😞";
      case "push": return "Push (tie). 🤝";
      default: return "Game over Check results!";
    }
  };

  return (
    <div className="game-wrapper">
      {tableId ? (
        <div className="blackjack-table">
          <h1>Blackjack</h1>
          <p><strong>Table ID</strong>
          </p>

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
