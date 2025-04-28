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

function calculateHandValue(cards) {
  let value = 0;
  let aceCount = 0;

  cards.forEach(card => {
    if (card.value === 'A') {
      aceCount++;
      value += 11;
    } else if (['K', 'Q', 'J'].includes(card.value)) {
      value += 10;
    } else {
      value += parseInt(card.value, 10);
    }
  });

  // Adjust for Aces if value is too high
  while (value > 21 && aceCount > 0) {
    value -= 10;
    aceCount--;
  }

  return value;
}

function BlackjackGame() {
  const [deck, setDeck] = useState(createDeck());
  const [playerHand, setPlayerHand] = useState([]);
  const [dealerHand, setDealerHand] = useState([]);
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState(null);
  const [showDealerCards, setShowDealerCards] = useState(false);
  const [isDealing, setIsDealing] = useState(false);

  const dealCards = () => {
    setIsDealing(true);
    setTimeout(() => {
      const newDeck = [...deck];
      const player = [newDeck.pop(), newDeck.pop()];
      const dealer = [newDeck.pop(), newDeck.pop()];
      setPlayerHand(player);
      setDealerHand(dealer);
      setDeck(newDeck);
      setGameOver(false);
      setWinner(null);
      setShowDealerCards(false);
      setIsDealing(false);
    }, 2000);
  };

  const handleHit = () => {
    if (gameOver) return;
    const newDeck = [...deck];
    const newCard = newDeck.pop();
    const newPlayerHand = [...playerHand, newCard];
    setPlayerHand(newPlayerHand);
    setDeck(newDeck);

    if (calculateHandValue(newPlayerHand) > 21) {
      setGameOver(true);
      setWinner('Dealer');
      setShowDealerCards(true);
    }
  };

  const handleStay = () => {
    if (gameOver) return;
    let newDeck = [...deck];
    let newDealerHand = [...dealerHand];

    while (calculateHandValue(newDealerHand) < 17) {
      newDealerHand.push(newDeck.pop());
    }

    const playerValue = calculateHandValue(playerHand);
    const dealerValue = calculateHandValue(newDealerHand);

    setDealerHand(newDealerHand);
    setDeck(newDeck);
    setShowDealerCards(true);

    if (dealerValue > 21 || playerValue > dealerValue) {
      setWinner('Player');
    } else if (dealerValue > playerValue) {
      setWinner('Dealer');
    } else {
      setWinner('Tie');
    }

    setGameOver(true);
  };

  const resetGame = () => {
    setDeck(createDeck());
    setPlayerHand([]);
    setDealerHand([]);
    setGameOver(false);
    setWinner(null);
    setShowDealerCards(false);
    setIsDealing(false);
  };

  return (
    <div style={{ textAlign: 'center' }}>
      <h1>Blackjack</h1>

      {/* Dealer's Hand */}
      <div className="player-dealer-section">
        <h2>Dealer's Hand</h2>
        {dealerHand.map((card, index) => (
          <span key={index} className="card-container">
            <div className={`card-inner ${showDealerCards || index === 0 ? 'card-flipped' : ''}`}>
              <div className="card-front">
                {card.value}{card.suit}
              </div>
              <div className="card-back"></div>
              <div className="card-shine"></div>
            </div>
          </span>
        ))}
        <p>
          {showDealerCards ? `Total: ${calculateHandValue(dealerHand)}` : 'Total: ??'}
        </p>
      </div>

      {/* Player's Hand */}
      <div className="player-dealer-section">
        <h2>Player's Hand</h2>
        {playerHand.map((card, index) => (
          <span key={index} className="card-container">
            <div className="card-inner">
              <div className="card-front">
                {card.value}{card.suit}
              </div>
              <div className="card-back"></div>
              <div className="card-shine"></div>
            </div>
          </span>
        ))}
        <p>Total: {calculateHandValue(playerHand)}</p>
      </div>

      {/* Game Controls */}
      <div style={{ margin: '20px' }}>
        {!gameOver ? (
          <>
            <button onClick={handleHit} disabled={isDealing}>Hit</button>
            <button onClick={handleStay} disabled={isDealing}>Stay</button>
            <button onClick={dealCards} disabled={isDealing}>Deal Cards</button>
          </>
        ) : (
          <>
            <h2>{winner === 'Tie' ? "It's a Tie!" : `${winner} Wins!`}</h2>
            <button onClick={resetGame}>Play Again</button>
          </>
        )}
      </div>
    </div>
  );
}

export default BlackjackGame;
