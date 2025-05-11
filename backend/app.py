from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import uuid
import random

app = Flask(__name__)

# Enable CORS for the frontend (React app running on localhost:3000) and supports credentials
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode="eventlet")

rooms = {}

# Event handlers and game logic as before
@socketio.on("join")
def handle_join(data):
    table_id = data["tableId"]
    if table_id not in rooms:
        emit("error", {"error": "Room does not exist."})
        return

    emit("game_state", {"message": "Player joined the game!"}, room=table_id)

@socketio.on("hit")
def handle_hit(data):
    table_id = data.get("tableId")
    if table_id not in rooms:
        emit("error", {"error": "Room does not exist."})
        return

    room = rooms[table_id]
    player_id = data.get("playerId")
    player = next((p for p in room["players"] if p["id"] == player_id), None)

    if not player:
        emit("error", {"error": "Player not found."})
        return
    if not room["deck"]:
        emit("error", {"error": "Deck is empty."})
        return

    card = room["deck"].pop()
    player["hand"].append(card)
    player["score"] = calculate_score(player["hand"])

    if player["score"] > 21:
        player["is_standing"] = True

    emit("game_state", {
        "player_hand": player["hand"],
        "score": player["score"],
        "current_turn": room["turn"],
        "game_over": all(p["is_standing"] for p in room["players"]),
        "players": room["players"],
    }, room=table_id)


@app.route("/")
def index():
    return "Server is running"

@app.route("/create-room", methods=["POST"])
def create_room():
    table_id = str(uuid.uuid4())[:8]
    rooms[table_id] = {
        "players": [],
        "started": False,
        "deck": [],
        "turn": None,
        "state": {}
    }
    return jsonify({"tableId": table_id, "message": "Room created successfully."}), 200

@app.route("/join-room", methods=["POST"])
def join_room():
    data = request.get_json()
    table_id = data.get("tableId")
    player_name = data.get("player_name")

    if table_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 404
    if len(rooms[table_id]["players"]) >= 2:
        return jsonify({"error": "Room is full."}), 403

    player_id = str(uuid.uuid4())[:8]
    player = {
        "id": player_id,
        "name": player_name,
        "hand": [],
        "score": 0,
        "is_standing": False
    }
    rooms[table_id]["players"].append(player)
    emit("game_state", {"message": f"{player_name} joined the room!"}, room=table_id)

    return jsonify({
        "message": "Joined room successfully.",
        "player_id": player_id,
        "room": rooms[table_id]
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
    table_id = data.get("tableId")
    room = rooms.get(table_id)

    if not rooms:
        return jsonify({"error": "Table not found."}), 404


    # Allow game to start with at least one player
    if len(room["players"]) < 1:
        return jsonify({"error": "Need at least 1 player to start."}), 400

    deck = create_deck()
    room["deck"] = deck
    room["started"] = True
    room["turn"] = room["players"][0]["id"]

    for player in room["players"]:
        player["hand"] = [deck.pop(), deck.pop()]
        player["score"] = calculate_score(player["hand"])

    emit("game_state", {
        "message": "Game started.",
        "players": room["players"],
        "deck": room["deck"],
        "current_turn": room["turn"],
        "game_over": False,
    }, room=table_id)

    return jsonify({"message": "Game started.", "room": room}), 200


@app.route("/hit", methods=["POST"])
def hit():
    data = request.get_json()
    table_id = data.get("tableId")
    player_id = data.get("player_id")

    if table_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 404
    room = rooms[table_id]
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

    emit("game_state", {
        "player_hand": player["hand"],
        "dealer_hand": room["deck"],
        "current_turn": room["turn"],
        "game_over": any(p["is_standing"] for p in room["players"]),
    }, room=table_id)

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
    table_id = data.get("tableId")
    player_id = data.get("player_id")

    if table_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 404
    room = rooms[table_id]
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
    }, room=table_id)

    return jsonify({
        "message": "Player stands.",
        "next_turn": room["turn"]
    }), 200

@app.route("/state", methods=["GET"])
def get_state():
    table_id = request.args.get("tableId")

    if table_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 400
    room = rooms[table_id]

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
        "tableId": table_id,
        "players": sanitized_players,
        "turn": room["turn"],
        "started": room["started"],
        "deck_count": len(room["deck"])
    }), 200


if __name__ == "__main__":
    print("✅ Registered routes:")
    print(app.url_map)
    socketio.run(app, debug=True, port=5001)