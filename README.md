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

## Project Structure

fullstack_blackjack_vite/
├── backend/ # Flask backend (API + Socket.IO server)
│ ├── app.py # Main Flask app with Socket.IO events
│ ├── requirements.txt # Python dependencies
├── public/ # Public assets for frontend
├── src/ # React frontend source code
│ ├── components/ # React components (game, chat, controls, etc.)
│ ├── socket.js # Socket.IO client setup
│ ├── main.jsx # React app entry point
│ ├── styles/ # CSS styles
├── package.json # Frontend dependencies and scripts
├── vite.config.js # Vite config
├── README.md # This file


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
