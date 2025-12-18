/* //fullstack_blackjack_vite/src/components/blackjack.jsx */


import React, { useEffect, useState, useCallback, useRef} from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BACKEND_URL } from '../config';
import socket from '../socket';
import DealerHand from './dealerhand';
import Controls from './controls';
import TableSeats from './tableseats';

import "../styles/lobby.css";
import "../styles/table.css";
import "../styles/cards.css";
import "../styles/buttons.css";



export default function BlackjackGame({ username, playerId }) {
  const { tableId } = useParams();
  const navigate = useNavigate();
  const playerIdStr = String(playerId);

  const [loading, setLoading] = useState(true);
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [opponentCards, setOpponentCards] = useState({});
  const [dealerReveal, setDealerReveal] = useState(false);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [gameState, setGameState] = useState({});
  const [betAmount, setBetAmount] = useState(10);
  const [joined, setJoined] = useState(false);

  const hasJoinedRef = useRef(false);

  /** Handles incoming game state from the server */
  const handleGameState = useCallback((state) => {
    console.log('received game_state:', state);
    console.log('full game_state:', JSON.stringify(state, null, 2));
    setGameState(state);

    const player = state?.players?.[playerIdStr] || null;
    console.log("player entry in state:", player);
    setPlayerCards(player?.hand || []);

    // Dealer hand
    if (state.reveal_dealer_hand) {
      setDealerCards([...(state.dealer?.hand || [])]);
      setDealerReveal(true);
    } else {
      const dealerHidden = (state.dealer?.hand || []).map((card, idx) =>
        idx === 0
        ? card
        : { value: "hidden",
            suit: "hidden",
            image: null,
            hidden: true
          }
      );
      setDealerCards(dealerHidden);
      setDealerReveal(false);
    }

    // Opponent hands
    const opponents = {};
    Object.entries(state.players || {}).forEach(([id, p]) => {
      if (id !== playerIdStr) {
        opponents[id] = state.reveal_hands
          ? (p.hand || []).map(card => ({ ...card }))
          : (p.hand || []).map(() => ({
            value: "hidden",
            suit: "hidden",
            image: null,
            hidden: true,
          }));
      }
    });
    setOpponentCards(opponents);

    // Turn and game over state
    setPlayerTurn(state.turn === playerIdStr);
    setGameOver(state.game_over);

    setLoading(false);
  }, [playerIdStr]);

  /** Socket connection + listeners */
  useEffect(() => {
    socket.on('connect', () => console.log('Connected to backend via Socket.IO'));
    socket.on('connect_error', err => console.error('Socket connection error:', err));
    socket.on('disconnect', () => console.warn('Socket disconnected'));
    socket.on('room_not_found', () => {
      alert("Room does not exist.");
      navigate("/");
    });
    socket.on('game_state', handleGameState);

    return () => {
      socket.off('connect');
      socket.off('connect_error');
      socket.off('disconnect');
      socket.off('room_not_found');
      socket.off('game_state', handleGameState);
    };
  }, [handleGameState, navigate]);

  /** Join table logic */
  useEffect(() => {
    if (!tableId || !playerIdStr || !username || hasJoinedRef.current) return;

    const doJoin = () => {
      console.log(">>> Attempting to join:", { tableId, playerId: playerIdStr, username });
      socket.emit(
        "join", {
        table_id: tableId,
        playerId: playerIdStr,
        username
      });

      socket.emit("chat_message", {
        table_id: tableId,
        playerId: playerIdStr,
        message: `Hello from ${username}!`,
        username,
      });

      hasJoinedRef.current = true; // prevent rejoin attempts
    };

    if (socket.connected) doJoin();
    else socket.once("connect", doJoin);

    return () => socket.off("connect", doJoin);
  }, [tableId, playerIdStr, username]);

  /** Room join acknowledgment */
  useEffect(() => {
    const handleJoinedRoom = (data) => {
      // Backend emmits: emit("joined_room", {table_id}, room=request.sid)
      const tableId = data?.table_id || data?.data?.table_id;

      if (!tableId) {
        console.warn("⚠️ joined_room event received with no table_id", payload);
        return;
      }
      console.log("✅ Successfully joined room:", tableId);
      setJoined(true);
    };
    socket.on('joined_room', handleJoinedRoom);
    return () => socket.off('joined_room', handleJoinedRoom);
  }, []);

  /** Bet placed listener */
  useEffect(() => {
    const handleBetPlaced = ({ playerId, bet }) => {
      console.log(`Player ${playerId} placed a bet of $${bet}`);
    };
    socket.on('bet_placed', handleBetPlaced);
    return () => socket.off('bet_placed', handleBetPlaced);
  }, []);

  /** Game control functions */
  const startGame = async () => {
    if (!tableId || !playerIdStr || !joined) {
      console.warn("Not ready to start game.");
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL}/start-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tableId, playerId: playerIdStr }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const data = await res.json();
      console.log("Response data:", data);
      console.log('Game started at table:', data.table_id);
    } catch (err) {
      console.error('Error starting game:', err);
    }
  };

  const hit = () => {
    console.log('Hit Clicked')
    socket.emit('hit', { table_id: tableId, playerId: playerIdStr });
  };

  const stay = () => {
    socket.emit('stay', { table_id: tableId, playerId: playerIdStr });
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
    socket.emit("place_bet", { tableId, playerId: playerIdStr, bet: betAmount });
  };

  const sendMessage = (msg) => {
    socket.emit('chat_message', {
      playerId: playerIdStr,
      username,
      tableId,
      message: msg,
    });
  };

  /** Betting restrictions */
  const numPlayers = gameState?.players ? Object.keys(gameState.players).length : 0;
  const allowBetting = numPlayers >= 2;

  useEffect(() => {
    if (!allowBetting) setBetAmount(10);
  }, [allowBetting]);

  const renderResult = () => {
    if (!gameOver) return null;
    const player = gameState.players?.[playerIdStr];
    if (!player?.result) return "Game over. Check results!";
    switch (player.result) {
      case "win": return "You won! 🎉";
      case "lose": return "You lost. 😞";
      case "push": return "Push (tie). 🤝";
      default: return "Game over. Check results!";
    }
  };

  /** Loading state */
  if (loading) {
    return <div className="loading-message">Loading game data...</div>;
  }

  /** Main UI */
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

                <DealerHand cards={dealerCards} reveal={dealerReveal} />

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
                      ? Object.entries(gameState.players).map(([pid, pData]) => ({
                          playerId: pid,
                          ...pData,
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
