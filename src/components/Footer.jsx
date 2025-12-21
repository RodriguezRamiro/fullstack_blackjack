/* //fullstack_blackjack_vite/src/components/Footer.jsx */

import React from 'react';

import '../styles/footer.css';

const Footer = () => {
    return (
        <footer className="footer" aria-label="Footer">
          <h3 className="footer-logo">RodriguezTech Studios&trade;</h3>
          <p>RodriguezTech. All rights reserved&reg; {new Date().getFullYear()} </p>
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