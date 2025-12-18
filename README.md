# Fullstack Blackjack (Vite + Flask)

A multiplayer Blackjack game with real-time gameplay and chat, built with React (Vite) frontend and Flask backend using Socket.IO for real-time communication.

---

## Features

- Multiplayer Blackjack gameplay
- Real-time game state updates via WebSockets (Socket.IO)
- Global and room-specific chat
- Clean UI built with React + Vite
- Backend API and WebSocket server with Flask + Flask-SocketIO

---

## Styling Architecture

Styles are organized by responsibility rather than component coupling:

- `variables.css` — design tokens
- `layout.css` — structural layout
- `buttons.css` — reusable UI elements
- Feature styles (`cards`, `chat`, `players`, etc.) scoped by domain

This keeps styles scalable and maintainable as the application grows.


## Project Structure

fullstack_blackjack_vite/
│
├── backend/
│   ├── app.py
│   ├── deck_api.py
│   ├── requirements.txt
│   ├── test_blackjack.py
│   └── test_scoring.py
│
├── public/
│
├── src/
│   ├── assets/
│   │   └── cardback.png
│   │
│   ├── components/
│   │   ├── blackjack.jsx
│   │   ├── controls.jsx
│   │   ├── dealerhand.jsx
│   │   ├── footer.jsx
│   │   ├── globalchat.jsx
│   │   ├── modal.jsx
│   │   ├── navbar.jsx
│   │   ├── playerhand.jsx
│   │   ├── playerseat.jsx
│   │   ├── roomchat.jsx
│   │   ├── tableseats.jsx
│   │   └── usernameprompt.jsx
│   │
│   ├── styles/
│   │   ├── index.css       # resets & globals
│   │   ├── variables.css   # colors, shadows, animation timings
│   │   ├── base.css        # body background, root layout
│   │   ├── layout.css      # page & column layout
│   │   ├── buttons.css
│   │   ├── lobby.css
│   │   ├── table.css
│   │   ├── players.css
│   │   ├── cards.css
│   │   ├── chat.css
│   │   ├── navbar.css
│   │   ├── footer.css
│   │   ├── modal.css
│   │   └── overlays.css
│   │
│   ├── app.jsx
│   ├── app.css
│   ├── main.jsx
│   ├── socket.js
│   └── config.js
│
├── .env
├── .env.production
├── .gitignore
├── eslint.config.js
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
└── README.md



---

## Getting Started

### Prerequisites

- Node.js (v16+ recommended)
- Python 3.10+
- `pip` for Python package management

---

### Setup Backend

1. Navigate to the backend folder:

```bash
cd backend

python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python app.py
By default, Flask-SocketIO uses eventlet or gevent for async support. Ensure eventlet is installed (it's in requirements).

Setup Frontend
Go back to the project root (if you aren’t there):

cd ..

Install frontend dependencies:

npm install

Run the React development server:
npm run dev
Open your browser at http://localhost:5173.

Deployment
Backend: Deploy the backend folder with Flask + Flask-SocketIO setup on your server or platform (Render, Heroku, etc.).

Frontend: Build the React app with
npm run build
and serve the static files using your choice of host or integrate with backend.

Contributing
Feel free to open issues or submit pull requests for bug fixes or new features!

License

MIT License

Copyright (c) 2025 Ramiro Rodriguez Alvarez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
