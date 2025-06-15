import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BACKEND_URL } from '../config';
import socket from '../socket';
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';
import TableSeats from './tableseats';

export default function BlackjackGame({ playerId, username }) {
  const { tableId } = useParams();
  const navigate = useNavigate();

  const playerIdStr = String(playerId);

  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [betAmount, setBetAmount] = useState(10);

  // Socket event listeners
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
      const player = state?.players?.[playerIdStr];
      setPlayerCards(player ? player.hand : []);
      setDealerCards(state.dealer?.hand || []);
      setPlayerTurn(player?.status === 'playing');
      setGameOver(state.game_over);
    });

    return () => {
      socket.off('connect');
      socket.off('connect_error');
      socket.off('disconnect');
      socket.off('room_not_found');
      socket.off('game_state');
    };
  }, [playerIdStr, navigate]);

  // Join table and send greeting on connect
  useEffect(() => {
    if (!tableId || !playerIdStr || !username) return;

    const handleConnect = () => {
      socket.emit("join", { tableId, playerId: playerIdStr, username });
      console.log(`Emitted join for player ${username} to room ${tableId}`);

      socket.emit('chat_message', {
        tableId,
        playerId: playerIdStr,
        message: `Hello from ${username}!`,
        username,
      });
    };

    if (socket.connected) {
      handleConnect();
    } else {
      socket.once('connect', handleConnect);
    }

    return () => {
      socket.off('connect', handleConnect);
    };
  }, [tableId, playerIdStr, username]);

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

  // Listen for bet_placed event
  useEffect(() => {
    const handleBetPlaced = ({ playerId, bet }) => {
      console.log(`Player ${playerId} placed a bet of $${bet}`);
      // Optional: update local state or show message
    };

    socket.on('bet_placed', handleBetPlaced);

    return () => {
      socket.off('bet_placed', handleBetPlaced);
    };
  }, []);

  // Functions for game actions
  const startGame = async () => {
    if (!tableId || !playerIdStr) {
      console.error('Missing tableId or playerId');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/start-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tableId, playerId: playerIdStr }),
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
    socket.emit('hit', { tableId, playerId: playerIdStr });
  };

  const stay = () => {
    socket.emit('stay', { tableId, playerId: playerIdStr });
  };

  const leaveTable = () => {
    if (window.confirm('Are you sure you want to leave the table?')) {
      socket.emit("leave", { tableId, playerId: playerIdStr });
      navigate("/");
    }
  };

  const placeBet = () => {
    if (!tableId || !playerIdStr || betAmount < 1) {
      console.error("Invalid bet or missing table/player ID");
      return;
    }

    socket.emit("place_bet", { tableId, playerId: playerIdStr, bet: betAmount }, (ack) => {
      console.log("Bet acknowledged by server:", ack);
    });
  };

  const sendMessage = (msg) => {
    socket.emit('chat_message', {
      tableId,
      playerId: playerIdStr,
      username,
      message: msg,
    });
  };

  // Render result message after game over
  const renderResult = () => {
    if (!gameOver) return null;
    if (!gameState || !gameState.players) return "Game over. Check results!";
    const player = gameState.players[playerIdStr];
    if (!player || !player.result) return "Game over. Check results!";

    switch (player.result) {
      case "win": return "You won! 🎉";
      case "lose": return "You lost. 😞";
      case "push": return "Push (tie). 🤝";
      default: return "Game over. Check results!";
    }
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
              currentPlayerId={playerIdStr}
              onSendMessage={sendMessage}
            />

            <DealerHand cards={dealerCards} />
            <PlayerHand cards={playerCards} username={username} />

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
