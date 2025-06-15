import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BACKEND_URL } from '../config';
import socket from '../socket';
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';
import RoomChat from './roomchat';
import PlayerSeat from './playerseat';
import TableSeats from './tableseats';

export default function BlackjackGame({ playerId, username }) {
  const { tableId } = useParams();
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [gameState, setGameState] = useState(null);
  const navigate = useNavigate();



  const players = [
    { playerId: '1', username: 'Alice', hand: [], chatBubble: 'Hi' },
    { playerId: '2', username: 'Bob', hand: [], chatBubble: null },
    { playerId: '3', username: 'Carol', hand: [], chatBubble: 'GL!' },
    { playerId: '4', username: 'Dave', hand: [], chatBubble: 'Let’s go!' }
  ];






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
      socket.off('room_not_found');
    };
  }, [playerId, navigate]);

  // Join table and send greeting
  useEffect(() => {
    if (!tableId || !playerId || !username) return;

    // Emit join
    socket.emit("join", { tableId, playerId, username });
    console.log(`Emitted join for player ${username} to room ${tableId}`);

    // Send greeting chat message
    socket.emit('chat_message', {
      tableId,
      playerId,
      message: `Hello from ${username}!`,
      username,
    });

  }, [tableId, playerId, username]);

  // Listen for joined_room confirmation (optional)
  useEffect(() => {
    const handleJoinedRoom = ({ tableId }) => {
      console.log(`Successfully joined room: ${tableId}`);
    };

    socket.on('joined_room', handleJoinedRoom);

    return () => {
      socket.off('joined_room', handleJoinedRoom);
    };
  }, []);

  useEffect(() => {
    socket.on('bet_placed', ({ playerId, bet}) =>{
      console.log(`Player ${playerId} placed a bet of $${bet}`);
      // Optional: update local state or show message
    });

    return () => {
      socket.off('bet_placed');
    };
  }, []);

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
    if (window.confirm('Are you sure you want to leave the table?')) {
      socket.emit("leave", { tableId, playerId });
      navigate("/");
    }
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
      default: return "Game over. Check results!";
    }
  };

  const [betAmount, setBetAmount] = useState(10); // default starting bet

  const placeBet = () => {
    if (!tableId || !playerId || betAmount < 1) {
      console.error("Invalid bet or missing table/player ID");
      return;
    }


    socket.emit("place_bet", { tableId, playerId, bet: betAmount }, (ack) => {
      console.log("Bet acknowledged by server:", ack);
    });
  };

  return (
    
    <div className="game-wrapper">
      {tableId ? (
        <div className="table-seats-layout">
          <div className="blackjack-table">
            <h1>Blackjack</h1>
            <div className="betting-controls">
              <label htmlFor="betAmount">Tables Bet ($): </label>
              <input
                id="betAmount"
                type="number"
                min="1"
                value={betAmount}
                onChange={(e) => setBetAmount(Number(e.target.value))}
                style={{ width: "80px", marginRight: "120px" }}
                disabled={playerTurn || gameOver}
              />
              <button onClick={placeBet} disabled={betAmount < 1 || playerTurn || gameOver}>
                Raise Bet
              </button>
            </div>
            <TableSeats
            players={gameState?.players ? Object.values(gameState.players) : []}
            currentPlayerId={playerId}
            onSendMessage={(msg) => {
              socket.emit('chat_message', {
                tableId,
                playerId,
                username,
                message: msg,
              });
            }}
          />

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
        </div>
      ) : (
        <p style={{ textAlign: 'center' }}>Waiting to join a table...</p>
      )}
    </div>
  );
}
