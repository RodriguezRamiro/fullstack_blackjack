// src/blackjack.jsx

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BACKEND_URL } from '../config';
import socket from '../socket';
import DealerHand from './dealerhand';
import Controls from './controls';
import TableSeats from './tableseats';
import '../styles/blackjackgame.css';

export default function BlackjackGame({ username, playerId }) {
  const { tableId } = useParams();
  const navigate = useNavigate();

  const playerIdStr = String(playerId);

  const [loading, setLoading] = useState(true);
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [dealerReveal, setDealerReveal] = useState(false);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [betAmount, setBetAmount] = useState(10);
  const [joined, setJoined] = useState(false);

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
      console.log('received game_state:', state);

      const player = state?.players?.[playerIdStr];
      if (player) {
        console.log(`Player hand cards count: ${player.hand?.length || 0}`, player.hand);
      } else {
        console.log('Player data not found in game state');
      }

      console.log('Dealer hand cards count:', state.dealer?.hand?.length || 0, state.dealer?.hand);

      setGameState(state);
      setLoading(false);

      console.log("Players in room:", Object.keys(state?.players || {}));

      setPlayerCards(player ? player.hand : []);
      setDealerCards(state.dealer?.hand || []);

      if (state.reveal_dealer_hand !== undefined) {
      setDealerReveal(state.reveal_dealer_hand);
  }

      const isMyTurn = state.current_turn === playerIdStr;
      setPlayerTurn(isMyTurn);

      setGameOver(state.game_over);

      console.log(`received game state. It's ${state.current_turn}'s turn. Is it your turn?`, isMyTurn);
});

    return () => {
      socket.off('connect');
      socket.off('connect_error');
      socket.off('disconnect');
      socket.off('room_not_found');
      socket.off('game_state');
    };
  }, [playerIdStr, navigate]);

  useEffect(() => {
    if (!tableId || !playerIdStr || !username || joined) return;
    console.log("Join condition check:", { tableId, playerIdStr, username, joined });

    const doJoin = () => {
      console.log(">>> Attempting to join with:", {
        tableId,
        playerId: playerIdStr,
        username,
      });

      socket.emit("join", { tableId, playerId: playerIdStr, username });

      socket.emit('chat_message', {
        tableId,
        playerId: playerIdStr,
        message: `Hello from ${username}!`,
        username,
      });
    };

    if (socket.connected) {
      doJoin();
    } else {
      socket.once("connect", doJoin);
    }

    return () => {
      socket.off("connect", doJoin);
    };
  }, [tableId, playerIdStr, username, joined]);

  useEffect(() => {
    const handleJoinedRoom = ({ tableId }) => {
      console.log(`Successfully joined room: ${tableId}`);
      setJoined(true);
    };

    socket.on('joined_room', handleJoinedRoom);

    return () => {
      socket.off('joined_room', handleJoinedRoom);
    };
  }, []);

  useEffect(() => {
    console.log("Joined:", joined, "GameState:", gameState);
  }, [joined, gameState]);

  useEffect(() => {
    const handleBetPlaced = ({ playerId, bet }) => {
      console.log(`Player ${playerId} placed a bet of $${bet}`);
    };

    socket.on('bet_placed', handleBetPlaced);

    return () => {
      socket.off('bet_placed', handleBetPlaced);
    };
  }, []);

  const startGame = async () => {
    if (!tableId || !playerIdStr || !joined) {
      console.warn("Not ready to start game: missing table ID, player ID or not joined yet.");
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
    setPlayerTurn(false); // locks out multiple hits
    socket.emit('hit', { tableId, playerId: playerIdStr });
  };

  const stay = () => {
    setPlayerTurn(false); // locks out multiple hits
    socket.emit('stay', { tableId, playerId: playerIdStr });
  };

  const leaveTable = () => {
    if (window.confirm('Are you sure you want to leave the table?')) {
      socket.emit("leave", { tableId, playerId: playerIdStr });
      navigate("/");
    }
  };

  const placeBet = () => {
    console.log("Placing Bet:", betAmount);
    if (!tableId || !playerIdStr || betAmount < 1) {
      console.error("Invalid bet or missing table/player ID");
      return;
    }

    socket.emit("place_bet", { tableId, playerId: playerIdStr, bet: betAmount }, (ack) => {
      console.log("Bet acknowledged by server:", ack);
    });
  };

  const sendMessage = (msg) => {
    const data = {
      playerId: playerIdStr,
      username,
      message: msg,
    };

    if (tableId) {
      data.tableId = tableId;
    }
    socket.emit('chat_message', data);
  };

  const numPlayers = gameState?.players ? Object.keys(gameState.players).length : 0;
  const allowBetting = numPlayers >= 2;

  useEffect(() => {
    console.log(`Players in game: ${numPlayers} — Allow betting: ${allowBetting}`);
  }, [numPlayers, allowBetting]);

  useEffect(() => {
    if (!allowBetting) {
      setBetAmount(10);
    }
  }, [allowBetting]);

  const renderResult = () => {
    if (!gameOver) return null;
    if (!gameState || !gameState.players) return "Game over. Check results!";
    const player = gameState.players[playerIdStr];
    if (!player || !player.result) return "Game over. Check results!";

    switch (player.result) {
      case "win":
        return "You won! 🎉";
      case "lose":
        return "You lost. 😞";
      case "push":
        return "Push (tie). 🤝";
      default:
        return "Game over. Check results!";
    }
  };

  if (loading) {
    return <div className="loading-message">Loading game data...</div>;
  }

  return (
    <div className="game-wrapper">
      {tableId ? (
        <div className="table-seats-layout">
          <div className="blackjack-table">
            <div className="blackjack-content">
              {/* LEFT SIDE — Game Area */}
              <div className="blackjack-left">
                <div className="betting-controls">
                  <label htmlFor="betAmount">Table Bet ($): </label>
                  <input
                    id="betAmount"
                    type="number"
                    min="1"
                    value={betAmount}
                    onChange={(e) => setBetAmount(Number(e.target.value))}
                    style={{ width: "80px", marginRight: "120px" }}
                    disabled={playerTurn || gameOver || !allowBetting}
                  />
                  <button
                    type="button"
                    onClick={placeBet}
                    disabled={betAmount < 1 || playerTurn || gameOver || !allowBetting}
                  >
                    Raise Bet
                  </button>
                  {!allowBetting && (
                    <p style={{ color: "orange", marginTop: "5px" }}>
                      Waiting for more players to join to enable betting.
                    </p>
                  )}
                </div>

                <DealerHand
                  cards={gameState?.dealer?.hand || []}
                  reveal={gameState?.reveal_dealer_hand}
                />

                <Controls
                  onDeal={startGame}
                  onHit={hit}
                  onStay={stay}
                  onReset={() => window.location.reload()}
                  disabled={!playerTurn || !joined}
                  gameOver={gameOver}
                  canDeal={true}
                />

                {gameOver && (
                  <div className="game-over-message">
                    <strong>{renderResult()}</strong>
                  </div>
                )}
              </div>

              {/* RIGHT SIDE — Chat / Players */}
              <div className="blackjack-right">
                <TableSeats
                  players={
                    gameState?.players
                      ? Object.entries(gameState.players).map(([playerId, playerData]) => ({
                          playerId,
                          ...playerData,
                        }))
                      : []
                  }
                  currentPlayerId={playerIdStr}
                  revealHands={dealerReveal}
                  onSendMessage={sendMessage}
                />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <p style={{ textAlign: 'center' }}>Waiting to join a table...</p>
      )}
    </div>
  );
}
