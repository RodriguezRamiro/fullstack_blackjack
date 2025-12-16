import React from 'react';

import '../styles/blackjackgame.css';

const Footer = () => {
    return (
        <footer className="footer" aria-label="Footer">
          <h3 className="footer-logo">RodriguezTech Solutions</h3>
          <p>&reg; {new Date().getFullYear()} RodriguezTech. All rights reserved.</p>
      <p>
        <small>
        All rights reserved - Version 1.0.0 —{' '}
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