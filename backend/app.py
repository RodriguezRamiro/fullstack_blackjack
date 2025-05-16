from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import random
import uuid
import requests

app = Flask(__name__)
app.secret_key = "Super-secret_key"
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode="eventlet")

rooms = {}


def create_deck():
    suits_map = {
        "SPADES": "♠",
        "HEARTS": "♥",
        "DIAMONDS": "♦",
        "CLUBS": "♣"
    }
    rank_map = {
        "ACE": "A",
        "KING": "K",
        "QUEEN": "Q",
        "JACK": "J"
    }

    # Fetch a full 52-card deck
    response = requests.get("https://deckofcardsapi.com/api/deck/new/draw/?count=52")
    if response.status_code != 200:
        raise Exception("Failed to fetch deck from external API.")

    cards = response.json()["cards"]

    return [
        {
            "suit": suits_map.get(card["suit"], card["suit"]),
            "rank": rank_map.get(card["value"], card["value"]),
            "image": card["image"]
        }
        for card in cards
    ]
def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        if card["rank"].isdigit():
            score += int(card["rank"])
        elif card["rank"] in ["J", "Q", "K"]:
            score += 10
        else:
            aces += 1
    for _ in range(aces):
        score += 11 if score + 11 <= 21 else 1
    return score

@app.route("/create-room", methods=["POST"])
def create_room():
    table_id = str(uuid.uuid4())
    if table_id in rooms:
        return jsonify({"error": "Room already exists"}), 400
    rooms[table_id] = {
        "players": {},
        "dealer": {"hand": [], "score": 0},
        "deck": create_deck(),
        "started": False,
        "game_over": False
    }
    return jsonify({"message": "Room created", "tableId": table_id})

@app.route("/start-game", methods=["POST"])
def start_game():
    data = request.get_json()
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    if not table_id or not player_id:
        return jsonify({"error": "Missing tableId or playerId."}), 404

    if table_id not in rooms:
        return jsonify({"error": "Room does not exist."}), 400

    room = rooms[table_id]

    if room["started"]:
        return jsonify({"message": "Game already started."}), 400

    if player_id not in room["players"]:
        return jsonify({"error": "Player not found in room."}), 400

    random.shuffle(room["deck"])

    for pid, info in room["players"].items():
        hand = [room["deck"].pop(), room["deck"].pop()]
        info.update({"hand": hand, "score": calculate_score(hand), "status": "playing"})

    room["dealer"]["hand"] = [room["deck"].pop()]
    room["dealer"]["score"] = calculate_score(room["dealer"]["hand"])
    room["started"] = True

    socketio.emit("game_state", {
        "players": room["players"],
        "dealer": room["dealer"],
        "deckCount": len(room["deck"]),
        "game_over": room["game_over"]
    }, room=table_id)

    return jsonify({"message": "Game started.", "tableId": table_id})

@socketio.on("join")
def handle_join(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    username = data.get("username")

    if not all([table_id, player_id, username]):
        return

    if table_id not in rooms:
        return

    room = rooms[table_id]
    if player_id not in room["players"]:
        room["players"][player_id] = {
            "username": username,
            "hand": [],
            "score": 0,
            "status": "waiting"
        }
    join_room(table_id)

    emit("game_state", {
        "players": room["players"],
        "dealer": room["dealer"],
        "deckCount": len(room["deck"]),
        "game_over": room["game_over"]
    }, room=table_id)

@socketio.on("hit")
def handle_hit(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    if table_id not in rooms or player_id not in rooms[table_id]["players"]:
        return

    room = rooms[table_id]
    card = room["deck"].pop()
    player = room["players"][player_id]
    player["hand"].append(card)
    player["score"] = calculate_score(player["hand"])

    if player["score"] > 21:
        player["status"] = "bust"

    emit("game_state", {
        "players": room["players"],
        "dealer": room["dealer"],
        "deckCount": len(room["deck"]),
        "game_over": room["game_over"]
    }, room=table_id)

@socketio.on("stay")
def handle_stay(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    if table_id not in rooms or player_id not in rooms[table_id]["players"]:
        return

    room = rooms[table_id]
    room["players"][player_id]["status"] = "stay"

    # Check if all players are done
    if all(p["status"] in ["bust", "stay"] for p in room["players"].values()):
        # Dealer plays
        while calculate_score(room["dealer"]["hand"]) < 17:
            room["dealer"]["hand"].append(room["deck"].pop())

        room["dealer"]["score"] = calculate_score(room["dealer"]["hand"])
        room["game_over"] = True

        # Determine results
        dealer_score = room["dealer"]["score"]
        for pid, p in room["players"].items():
            if p["status"] == "bust":
                p["result"] = "lose"
            elif dealer_score > 21 or p["score"] > dealer_score:
                p["result"] = "win"
            elif p["score"] == dealer_score:
                p["result"] = "push"
            else:
                p["result"] = "lose"

    emit("game_state", {
        "players": room["players"],
        "dealer": room["dealer"],
        "deckCount": len(room["deck"]),
        "game_over": room["game_over"]
    }, room=table_id)

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected.")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
