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

  useEffect(() => {
    fetch(`${API_BASE}/new/shuffle/?deck_count=1`)
      .then(res => res.json())
      .then(data => setDeckId(data.deck_id));
  }, []);

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
      aceCount -= 1;
    }

    return value;
  };

  const dealCards = async () => {
    if (!deckId) return;
    const draw = await fetch(`${API_BASE}/${deckId}/draw/?count=4`);
    const data = await draw.json();
    setPlayerCards([data.cards[0], data.cards[2]]);
    setDealerCards([data.cards[1], data.cards[3]]);
    setGameOver(false);
  };

  const hitCard = async () => {
    if (!deckId || gameOver) return;

    const draw = await fetch(`${API_BASE}/${deckId}/draw/?count=1`);
    const data = await draw.json();
    const newHand = [...playerCards, data.cards[0]];
    setPlayerCards(newHand);

    if (calculateHandValue(newHand) > 21) {
      setGameOver(true);
    }
  };

  const stay = async () => {
    if (!deckId || gameOver) return;

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
    const shuffleResponse = await fetch(`${API_BASE}/new/shuffle/?deck_count=1`);
    const shuffleData = await shuffleResponse.json();
    setDeckId(shuffleData.deck_id);
    setPlayerCards([]);
    setDealerCards([]);
    setGameOver(false);
  };

  return (
    <div className="blackjack-table">
      <h1>Blackjack</h1>
      <DealerHand cards={dealerCards} />
      <PlayerHand cards={playerCards} />
      <Controls
  onDeal={dealCards}
  onHit={hitCard}
  onStay={stay}
  onReset={resetGame}
  disabled={playerCards.length === 0 || gameOver}
  gameOver={gameOver}
/>
      {gameOver && (
        <div className="game-over-message">
          {calculateHandValue(playerCards) > 21
            ? 'You busted! Game over!'
            : calculateHandValue(dealerCards) > 21
            ? 'Dealer busted! You win!'
            : calculateHandValue(playerCards) > calculateHandValue(dealerCards)
            ? 'You win!'
            : calculateHandValue(playerCards) === calculateHandValue(dealerCards)
            ? 'It\'s a tie!'
            : 'Dealer wins!'}
        </div>
      )}
    </div>
  );
}
