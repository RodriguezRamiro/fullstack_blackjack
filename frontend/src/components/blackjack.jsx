// blackjack.jsx


import React, { useEffect, useState } from 'react';
import DealerHand from './dealerhand';
import PlayerHand from './playerhand';
import Controls from './controls';
import '../styles/blackjackgame.css';

const API_BASE = 'https://deckofcardsapi.com/api/deck';

export default function BlackjackGame() {
  const [deckId, setDeckId] = useState(null);
  const [playerCards, setPlayerCards] = useState([]);
  const [dealerCards, setDealerCards] = useState([]);
  const [gameOver, setGameOver] = useState(false);
  const [playerTurn, setPlayerTurn] = useState(false); // new state

  // Fetch deck on mount
  useEffect(() => {
    fetchNewDeck();
  }, []);

  const fetchNewDeck = async () => {
    try {
      const res = await fetch(`${API_BASE}/new/shuffle/?deck_count=1`);
      const data = await res.json();
      console.log('Fetched deck:', data);
      setDeckId(data.deck_id);
    } catch (err) {
      console.error('Failed to fetch new deck:', err);
    }
  };

  const calculateHandValue = (cards) => {
    let value = 0;
    let aceCount = 0;

    cards.forEach(card => {
      if (['KING', 'QUEEN', 'JACK'].includes(card.value)) {
        value += 10;
      } else if (card.value === 'ACE') {
        value += 11;
        aceCount += 1;
      } else {
        value += parseInt(card.value);
      }
    });

    while (value > 21 && aceCount > 0) {
      value -= 10;
      aceCount--;
    }

    return value;
  };

  const dealCards = async () => {
    if (!deckId) return;
    try {
      const res = await fetch(`${API_BASE}/${deckId}/draw/?count=4`);
      const data = await res.json();
      console.log('Dealt cards:', data);
      if (data.success) {
        setPlayerCards([data.cards[0], data.cards[2]]);
        setDealerCards([data.cards[1], data.cards[3]]);
        setGameOver(false);
        setPlayerTurn(true);
      } else {
        console.error('Card draw failed:', data);
      }
    } catch (err) {
      console.error('Deal error:', err);
    }
  };

  const hitCard = async () => {
    if (!deckId || !playerTurn) return;

    const res = await fetch(`${API_BASE}/${deckId}/draw/?count=1`);
    const data = await res.json();
    const updatedHand = [...playerCards, data.cards[0]];
    setPlayerCards(updatedHand);

    const total = calculateHandValue(updatedHand);
    if (total > 21) {
      setGameOver(true);
      setPlayerTurn(false);
    }
  };

  const stay = async () => {
    if (!deckId || !playerTurn) return;

    setPlayerTurn(false);
    let dealerHand = [...dealerCards];
    let dealerTotal = calculateHandValue(dealerHand);

    while (dealerTotal < 17) {
      const res = await fetch(`${API_BASE}/${deckId}/draw/?count=1`);
      const data = await res.json();
      dealerHand.push(data.cards[0]);
      dealerTotal = calculateHandValue(dealerHand);
    }

    setDealerCards(dealerHand);
    setGameOver(true);
  };

  const resetGame = async () => {
    await fetchNewDeck();
    setPlayerCards([]);
    setDealerCards([]);
    setGameOver(false);
    setPlayerTurn(false);
  };

  const renderResult = () => {
    const playerValue = calculateHandValue(playerCards);
    const dealerValue = calculateHandValue(dealerCards);

    if (playerValue > 21) return 'You busted! Game over!';
    if (dealerValue > 21) return 'Dealer busted! You win!';
    if (playerValue > dealerValue) return 'You win!';
    if (playerValue === dealerValue) return "It's a tie!";
    return 'Dealer wins!';
  };

  return (
    <div className="game-wrapper">
      <div className="blackjack-table">
        <h1>Blackjack</h1>
        <DealerHand cards={dealerCards} />
        <PlayerHand cards={playerCards} />
        <Controls
          onDeal={dealCards}
          onHit={hitCard}
          onStay={stay}
          onReset={resetGame}
          disabled={!playerTurn}
          gameOver={gameOver}
        />
        {gameOver && <div className="game-over-message">{renderResult()}</div>}
      </div>

      <div className="avatar-ring">
        {[...Array(5)].map((_, idx) => (
          <div key={idx} className={`avatar-placeholder avatar-${idx}`} />
        ))}
      </div>
    </div>
  );
        }
