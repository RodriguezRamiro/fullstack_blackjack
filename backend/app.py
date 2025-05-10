from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import uuid

app = Flask(__name__)
CORS(app)

# WebSocket setup with CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# In-memory storage for game rooms
rooms = {}

@app.route("/")
def index():
    return "Server is running"

@app.route("/create-room", methods=["POST"])
def create_room():
    room_id = str(uuid.uuid4())[:8]  # Short unique room ID
    rooms[room_id] = {
        "players": [],
        "started": False,
        "deck": [],
        "turn": None,
        "state": {}
    }
    return jsonify({
        "room_id": room_id,
        "message": "Room created successfully."
    }), 200

@app.route("/join-room", methods=["POST"])
def join_room():
    data = request.get_json()
    room_id = data.get("room_id")
    player_name = data.get("player_name")

    if room_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 404

    if len(rooms[room_id]["players"]) >= 2:
        return jsonify({"error": "Room is full."}), 403

    player_id = str(uuid.uuid4())[:8]
    player = {
        "id": player_id,
        "name": player_name,
        "hand": [],
        "score": 0,
        "is_standing": False
    }

    rooms[room_id]["players"].append(player)
    return jsonify({
        "message": "Joined room successfully.",
        "player_id": player_id,
        "room": rooms[room_id]
    }), 200

# Sample WebSocket event to test communication
@socketio.on("test")
def handle_test(data):
    print("Received test message:", data)
    socketio.emit("test_response", {"message": "Hello from server!"})

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)
