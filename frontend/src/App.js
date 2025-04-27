import logo from './logo.svg';
import './App.css';
import BlackJackGame from './components/blackjack';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          <BlackJackGame />
        </p>

      </header>
    </div>
  );
}

export default App;
