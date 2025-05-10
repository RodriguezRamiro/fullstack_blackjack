// blackjack.jsx


import React, { useEffect, useState } from 'react';
import socket from '../socket'; // assuming you saved it as shown
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';
import Chatbox from './chatbox';

export default function BlackjackGame() {
  const [roomId, setRoomId] = useState(null);
  const [playerId, setPlayerId] = useState(null);
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);

  useEffect(() => {
    // Connect and set up listeners
    socket.on("connect", () => {
      console.log("Connected to backend via Socket.IO");
    });

    // Listen for the game state update from the backend
    socket.on("game_state", (state) => {
      setPlayerCards(state.player_hand || []);
      setDealerCards(state.dealer_hand || []);
      setPlayerTurn(state.current_turn === playerId);
      setGameOver(state.game_over);
    });

    // Receive playerId from server
    socket.on("player_id", (id) => {
      setPlayerId(id);
    });

    // Cleanup on unmount
    return () => {
      socket.off("connect");
      socket.off("game_state");
      socket.off("player_id");
    };
  }, [playerId]);

  const createRoom = async () => {
    try {
      const res = await fetch("http://localhost:5001/create-room", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json", // Ensure the correct headers are included
        },
      });

      if (!res.ok) {
        // If the response is not OK, throw an error
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setRoomId(data.room_id);
      socket.emit("join", { room_id: data.room_id });  // Emit room creation event
    } catch (error) {
      console.error("Error creating room:", error);
      // Optionally, you can show a user-friendly message
    }
  };


  const joinRoom = async (room) => {
    const res = await fetch("http://localhost:5001/join-room", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_id: room }),
      credentials: "include"
    });
    const data = await res.json();
    setRoomId(room);
    socket.emit("join", { room_id: room });
  };

  const startGame = async () => {
    await fetch("http://localhost:5001/start-game", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_id: roomId }),
      credentials: "include"
    });
  };

  const hit = async () => {
    await fetch("http://localhost:5001/hit", {
      method: "POST",
      credentials: "include"
    });
  };

  const stay = async () => {
    await fetch("http://localhost:5001/stay", {
      method: "POST",
      credentials: "include"
    });
  };

  const renderResult = () => {
    return gameOver ? "Game over. Check results!" : null;
  };

  return (
    <div className="game-wrapper">
      <div className="blackjack-table">
        <h1>Multiplayer Blackjack</h1>
        {!roomId && (
          <>
            <button onClick={createRoom}>Create Room</button>
            <button onClick={() => joinRoom(prompt("Enter Room ID"))}>Join Room</button>
          </>
        )}

        {roomId && (
          <>
            <DealerHand cards={dealerCards} />
            <PlayerHand cards={playerCards} />
            <Controls
              onDeal={startGame}
              onHit={hit}
              onStay={stay}
              onReset={() => setRoomId(null)}
              disabled={!playerTurn}
              gameOver={gameOver}
              canDeal={true}
            />
            {gameOver && <div className="game-over-message"><strong>{renderResult()}</strong></div>}
          </>
        )}
      </div>
      <Chatbox socket={socket} roomId={roomId} />
    </div>
  );
}
