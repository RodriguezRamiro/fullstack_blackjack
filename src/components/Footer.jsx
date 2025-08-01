import React from 'react';

import '../styles/blackjackgame.css';

const Footer = () => {
    return (
        <footer className="footer" aria-label="Footer">
      <p>© 2025 Ramiro Rodriguez Alvarez</p>
      <p>
        <small>
          Version 1.0.0 —{' '}
          <a
            href="https://github.com/RodriguezRamiro/DevsLanding"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on GitHub
          </a>
        </small>
      </p>
    </footer>

    );
};

export default Footer;