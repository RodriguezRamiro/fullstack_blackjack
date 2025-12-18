import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';
import './styles/variables.css';

import './styles/layout.css';
import './styles/buttons.css';

import './styles/lobby.css';
import './styles/table.css';
import './styles/players.css';
import './styles/cards.css';
import './styles/chat.css';
import './styles/overlays.css';


ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
