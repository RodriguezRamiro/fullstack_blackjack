import React, { useState } from 'react';
import '../styles/blackjackgame.css';

const suits = ['♠', '♥', '♦', '♣'];
const values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

function createDeck() {
  const deck = [];
  suits.forEach((suit) => {
    values.forEach((value) => {
      deck.push({ suit, value });
    });
  });
  return shuffle(deck);
}

function shuffle(array) {
  return array.sort(() => Math.random() - 0.5);
}

function calculateHandValue(hand) {
  let value = 0;
  let aces = 0;
  hand.forEach(card => {
    if (['J', 'Q', 'K'].includes(card.value)) {
      value += 10;
    } else if (card.value === 'A') {
      value += 11;
      aces += 1;
    } else {
      value += parseInt(card.value);
    }
  });
  while (value > 21 && aces > 0) {
    value -= 10;
    aces -= 1;
  }
  return value;
}

function BlackjackGame() {
  const [deck, setDeck] = useState(createDeck());
  const [playerHand, setPlayerHand] = useState([]);
  const [dealerHand, setDealerHand] = useState([]);
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState(null);
  const [showDealerCards, setShowDealerCards] = useState(false); // <-- NEW

  function dealInitialCards() {
    const newDeck = [...deck];
    const player = [newDeck.pop(), newDeck.pop()];
    const dealer = [newDeck.pop(), newDeck.pop()];
    setPlayerHand(player);
    setDealerHand(dealer);
    setDeck(newDeck);
    setGameOver(false);
    setWinner(null);
    setShowDealerCards(false); // hide dealer's cards at start
  }

  function handleHit() {
    if (gameOver) return;
    const newDeck = [...deck];
    const newCard = newDeck.pop();
    const newPlayerHand = [...playerHand, newCard];
    setPlayerHand(newPlayerHand);
    setDeck(newDeck);

    if (calculateHandValue(newPlayerHand) > 21) {
      setGameOver(true);
      setWinner('Dealer');
      setShowDealerCards(true); // reveal dealer's cards
    }
  }

  function handleStay() {
    if (gameOver) return;
    let newDeck = [...deck];
    let newDealerHand = [...dealerHand];

    // Dealer hits until 17+
    while (calculateHandValue(newDealerHand) < 17) {
      newDealerHand.push(newDeck.pop());
    }

    const playerValue = calculateHandValue(playerHand);
    const dealerValue = calculateHandValue(newDealerHand);

    setDealerHand(newDealerHand);
    setDeck(newDeck);
    setShowDealerCards(true); // <-- reveal cards when player stays

    if (dealerValue > 21 || playerValue > dealerValue) {
      setWinner('Player');
    } else if (dealerValue > playerValue) {
      setWinner('Dealer');
    } else {
      setWinner('Tie');
    }

    setGameOver(true);
  }

  return (
    <div style={{ textAlign: 'center' }}>
      <h1>Blackjack</h1>
      <div>
  <h2>Dealer's Hand</h2>
  {dealerHand.map((card, index) => (
    <span key={index} className="card-container">
      <div className={`card-inner ${(index !== 0 && showDealerCards) ? 'card-flipped' : ''}`}>
        {/* Front of the card */}
        <div className="card-front">
          {card.value}{card.suit}
        </div>
        {/* Back of the card */}
        <div className="card-back">
        </div>
         {/* ✨ Shine effect ✨ */}
  <div className="card-shine">
  </div>
      </div>
    </span>
  ))}
  <p>
    {showDealerCards ? `Total: ${calculateHandValue(dealerHand)}` : 'Total: ??'}
  </p>
</div>


<div>
  <h2>Player's Hand</h2>
  {playerHand.map((card, index) => (
    <span key={index}>
      <div className="card">{card.value}{card.suit}</div>
    </span>
  ))}
  <p>Total: {calculateHandValue(playerHand)}</p>
</div>

      <div style={{ margin: '20px' }}>
        {!gameOver && (
          <>
            <button onClick={handleHit}>Hit</button>
            <button onClick={handleStay}>Stay</button>
          </>
        )}
        {gameOver && (
          <>
            <h2>{winner === 'Tie' ? "It's a Tie!" : `${winner} Wins!`}</h2>
            <button onClick={dealInitialCards}>Play Again</button>
          </>
        )}
      </div>
    </div>
  );
}

export default BlackjackGame;
