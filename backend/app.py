from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import uuid
import random

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

rooms = {}

@socketio.on("join")
def handle_join(data):
    room_id = data["room_id"]
    # You could add logic to track player joining the room here
    emit("game_state", {"message": "Player joined the game!"}, room=room_id)

@socketio.on("hit")
def handle_hit(data):
    room_id = data.get("room_id")  # Corrected this
    if room_id not in rooms:
        return  # Handle error if room does not exist

    room = rooms[room_id]
    player_id = data.get("player_id")
    player = next((p for p in room["players"] if p["id"] == player_id), None)

    if not player:
        return jsonify({"error": "Player not found."}), 404
    if not room["deck"]:
        return jsonify({"error": "Deck is empty."}), 404

    card = room["deck"].pop()
    player["hand"].append(card)
    player["score"] = calculate_score(player["hand"])

    if player["score"] > 21:
        player["is_standing"] = True
        # Optional: end game logic

    emit("game_state", {
        "player_hand": player["hand"],
        "dealer_hand": room["deck"],
        "current_turn": room["turn"],
        "game_over": any(p["is_standing"] for p in room["players"]),
    }, room=room_id)

@app.route("/")
def index():
    return "Server is running"

@app.route("/create-room", methods=["POST"])
def create_room():
    print("Received request to create room")
    room_id = str(uuid.uuid4())[:8]
    rooms[room_id] = {
        "players": [],
        "started": False,
        "deck": [],
        "turn": None,
        "state": {}
    }
    print(f"Room {room_id} created")
    return jsonify({"room_id": room_id, "message": "Room created successfully."}), 200

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
    emit("game_state", {"message": f"{player_name} joined the room!"}, room=room_id)

    return jsonify({
        "message": "Joined room successfully.",
        "player_id": player_id,
        "room": rooms[room_id]
    }), 200

def create_deck():
    suits = ['♠', '♥', '♦', '♣']
    values = list(range(2, 11)) + ['J', 'Q', 'K', 'A']
    deck = [f"{v}{s}" for v in values for s in suits]
    random.shuffle(deck)
    return deck

def calculate_score(hand):
    value = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']:
            value += 10
        elif rank == 'A':
            aces += 1
            value += 11
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

@app.route("/start-game", methods=["POST"])
def start_game():
    data = request.get_json()
    room_id = data.get("room_id")

    if room_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 404
    room = rooms[room_id]
    if len(room["players"]) < 2:
        return jsonify({"error": "Need 2 players to start."}), 400

    deck = create_deck()
    room["deck"] = deck
    room["started"] = True
    room["turn"] = room["players"][0]["id"]

    for player in room["players"]:
        player["hand"] = [deck.pop(), deck.pop()]
        player["score"] = calculate_score(player["hand"])

    return jsonify({"message": "Game started.", "room": room}), 200

@app.route("/hit", methods=["POST"])
def hit():
    data = request.get_json()
    room_id = data.get("room_id")
    player_id = data.get("player_id")

    if room_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 404
    room = rooms[room_id]
    if room["turn"] != player_id:
        return jsonify({"error": "Not your turn."}), 403

    player = next((p for p in room["players"] if p["id"] == player_id), None)
    if not player:
        return jsonify({"error": "Player not found."}), 404
    if not room["deck"]:
        return jsonify({"error": "Deck is empty."}), 404

    card = room["deck"].pop()
    player["hand"].append(card)
    player["score"] = calculate_score(player["hand"])

    if player["score"] > 21:
        player["is_standing"] = True
        # Optional: end game logic

    emit("game_state", {
        "player_hand": player["hand"],
        "dealer_hand": room["deck"],
        "current_turn": room["turn"],
        "game_over": any(p["is_standing"] for p in room["players"]),
    }, room=room_id)

    return jsonify({
        "message": "Card dealt.",
        "card": card,
        "hand": player["hand"],
        "score": player["score"],
        "busted": player["score"] > 21
    }), 200

@app.route("/stay", methods=["POST"])
def stay():
    data = request.get_json()
    room_id = data.get("room_id")
    player_id = data.get("player_id")

    if room_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 404
    room = rooms[room_id]
    if room["turn"] != player_id:
        return jsonify({"error": "Not your turn."}), 403

    player = next((p for p in room["players"] if p["id"] == player_id), None)
    if not player:
        return jsonify({"error": "Player not found."}), 404

    player["is_standing"] = True

    other_players = [p for p in room["players"] if p["id"] != player_id]
    if other_players and not other_players[0]["is_standing"]:
        room["turn"] = other_players[0]["id"]
    else:
        room["turn"] = None  # Game over, determine winner soon

    emit("game_state", {
        "message": f"{player['name']} stands.",
        "next_turn": room["turn"]
    }, room=room_id)

    return jsonify({
        "message": "Player stands.",
        "next_turn": room["turn"]
    }), 200

@app.route("/state", methods=["GET"])
def get_state():
    room_id = request.args.get("room_id")

    if room_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 400
    room = rooms[room_id]

    sanitized_players = [
        {
            "id": p["id"],
            "name": p["name"],
            "hand": p["hand"],
            "score": p["score"],
            "is_standing": p["is_standing"]
        } for p in room["players"]
    ]

    return jsonify({
        "room_id": room_id,
        "players": sanitized_players,
        "turn": room["turn"],
        "started": room["started"],
        "deck_count": len(room["deck"])
    }), 200

@socketio.on("test")
def handle_test(data):
    print("Received test message:", data)
    socketio.emit("test_response", {"message": "Hello from server!"})

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)
