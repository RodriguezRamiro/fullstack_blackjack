// blackjack.jsx


import React, { useEffect, useState } from 'react';
import socket from '../socket';
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';
import Chatbox from './chatbox';

export default function BlackjackGame() {
  const [tableId, setTableId] = useState(null);
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

    socket.on("game_state", (state) => {
      setPlayerCards(state.player_hand || []);
      setDealerCards(state.dealer_hand || []);
      setPlayerTurn(state.current_turn === playerId);
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
  }, [playerId]);

  const createTable = async () => {
    try {
      const res = await fetch("/create-room", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

      const data = await res.json();
      console.log("Created Room:", data);

      setTableId(data.tableId);
      console.log("Emitting join event for table:", data.tableId);

      socket.emit("join", { tableId: data.tableId });
    } catch (error) {
      console.error("Error creating table:", error);
    }
  };

  const joinTable = async (table) => {
    try {
      const res = await fetch("http://localhost:5001/join-room", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tableId: table }),
        credentials: "include"
      });

      const data = await res.json();
      setTableId(table);
      console.log("Emitting join event for table:", data.tableId);
      socket.emit("join", { tableId: data.tableId });
    } catch (error) {
      console.error("Error joining table:", error);
    }
  };

  const startGame = async () => {
    try {
      const response = await fetch('http://localhost:5001/start-game', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tableId: tableId }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to start the game');
      }
      const data = await response.json();
      console.log('Game started', data);
    } catch (error) {
      console.error('Error starting the game:', error);
    }
  };

  const hit = async () => {
    await fetch("http://localhost:5001/hit", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tableId: tableId, playerId: playerId }),
      credentials: "include"
    });
  };

  const stay = async () => {
    await fetch("http://localhost:5001/stay", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tableId: tableId, playerId: playerId }),
      credentials: "include"
    });
  };

  const renderResult = () => {
    return gameOver ? "Game over. Check results!" : null;
  };

  return (
    <div className="game-wrapper">
      <div className="blackjack-table">
        <h1>Blackjack</h1>

        {!tableId && (
          <>
            <button onClick={createTable}>Create Table</button>
            <button onClick={() => joinTable(prompt("Enter Table ID"))}>Join Table</button>
          </>
        )}

        {tableId && (
          <>
            <p><strong>Table ID:</strong> {tableId}</p>
            <button className='copy-button' onClick={() => {
              navigator.clipboard.writeText(tableId);}}
              title="Copy Table ID">📋</button>
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
          </>
        )}
      </div>

      <Chatbox socket={socket} roomId={tableId} />
    </div>
  );
}
