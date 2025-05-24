// blackjack.jsx


import React, { useEffect, useState } from 'react';
import socket from '../socket';
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';
import Chatbox from './chatbox';

export default function BlackjackGame() {
  const [hasJoined, setHasJoined] = useState(false);
  const [tableId, setTableId] = useState(null);
  const [playerId, setPlayerId] = useState(() => crypto.randomUUID());
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [playerTurn, setPlayerTurn] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [username] = useState("Player");

  useEffect(() => {
    socket.on("connect", () => {
      console.log("Connected to backend via Socket.IO");
    });

    socket.on("game_state", (state) => {
      const player = state.players[playerId];
      setPlayerCards(player ? player.hand : []);
      setDealerCards(state.dealer.hand);
      setPlayerTurn(player ? player.status === 'playing' : false);
      setGameOver(state.game_over);
    });

    socket.on("player_id", (id) => {
      setPlayerId(id);
    });

    return () => {
      socket.off("connect");
      socket.off("game_state");
      socket.off("player_id");
    };
  }, []);

  const createTable = async () => {
    try {
      const res = await fetch("/create-room", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
      });

      const data = await res.json();
      setTableId(data.tableId);
      socket.emit("join", { tableId: data.tableId, playerId, username });
      setHasJoined(true);
    } catch (error) {
      console.error("Error creating table:", error);
    }
  };

  const joinTable = (incomingTableId) => {
    setTableId(incomingTableId);
    socket.emit("join", { tableId: incomingTableId, playerId, username });
    setHasJoined(true);
    console.log("Emitting join with username:", username);

  };

  const startGame = async () => {
    console.log('Attempting to start game with:');
  console.log('tableId:', tableId);
  console.log('playerId:', playerId);


  if (!tableId || !playerId) {
    console.error('Missing tableId or playerId');
    return;
  }

    try {
      const response = await fetch('http://localhost:5001/start-game', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tableId, playerId }),
        credentials: 'include',
      });

      const data = await response.json();
      console.log('Game started at table:', data.tableId);
    } catch (error) {
      console.error('Error starting the game:', error);
    }
  };



  const hit = async () => {
    socket.emit("hit", { tableId, playerId });
  };

  const stay = async () => {
    socket.emit("stay", { tableId, playerId });
  };

  const renderResult = () => {
    return gameOver ? "Game over. Check results!" : null;
  };

  return (
    <div className="game-wrapper">
      {tableId ? (
        <>
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
              onReset={() => setTableId(null)}
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

          {hasJoined && (
            <Chatbox
              socket={socket}
              tableId={tableId}
              playerId={playerId}
              username={username || "Player"}
            />
          )}
        </>
      ) : (
        <>
          <h1>Blackjack</h1>
          <button onClick={createTable}>Create Table</button>
          <button onClick={() => joinTable(prompt("Enter Table ID"))}>
            Join Table
          </button>
        </>
      )}
    </div>
  );
}