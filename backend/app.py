from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room, emit, rooms
import eventlet
import eventlet.wsgi
import os
from flask_cors import CORS
import random
import uuid
import requests

port = int(os.environ.get("PORT", 5001))

app = Flask(__name__)
app.secret_key = "Super-secret_key"

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://fullstack-blackjack.vercel.app"
]

CORS(app, supports_credentials=True, origins=allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode="eventlet")

game_rooms = {}




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
    if table_id in game_rooms:  # You had "rooms" which is the socketio helper, changed to game_rooms (your dict)
        return jsonify({"error": "Room already exists"}), 400
    game_rooms[table_id] = {
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

    if table_id not in game_rooms:
        return jsonify({"error": "Room does not exist."}), 400

    room = game_rooms[table_id]

    if player_id not in room["players"]:
        return jsonify({"error": "Player not found in room."}), 400

    if room["started"] and not room["game_over"]:
        return jsonify({"message": "Game already in progress."}), 400

    #Reset the game state regardless of current game status
    room["deck"] = create_deck()
    random.shuffle(room["deck"])
    room["game_over"] = False

    random.shuffle(room["deck"])

    for pid, info in room["players"].items():
        hand = [room["deck"].pop(), room["deck"].pop()]
        info.update({"hand": hand, "score": calculate_score(hand), "status": "playing"})

    room["dealer"] = {
    "hand": [room["deck"].pop()],
    "score": 0
}
    room["dealer"]["score"] = calculate_score(room["dealer"]["hand"])

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
        print("Join failed: missing data", data)
        return

    print(f"{username} joined room {table_id}")

    if table_id not in game_rooms:
        print("Room does not exist:", table_id)
        return

    room = game_rooms[table_id]
    if player_id not in room["players"]:
        room["players"][player_id] = {
            "username": username,
            "hand": [],
            "score": 0,
            "status": "waiting"
        }

    join_room(table_id)

    current_rooms = rooms(request.sid)  # this returns a set of rooms user is in
    for r in current_rooms:
        if r != request.sid and r != table_id:
            leave_room(r)
            print(f"Left room: {r}")

    emit("joined_room", {"tableId": table_id}, to=request.sid)

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

    if table_id not in game_rooms or player_id not in game_rooms[table_id]["players"]:  # ✅
        return

    room = game_rooms[table_id]

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

    if table_id not in game_rooms or player_id not in game_rooms[table_id]["players"]:  # ✅
        return

    room = game_rooms[table_id]
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


@socketio.on("chat_message")
def handle_chat_message(data):
    print("Chat received:", data)  # debug
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    message = data.get("message")
    username = data.get("username", "Anonymous")


    # Skip empty messages
    if not message:
        return

    is_global = True

    # If table_id exists and player is in the room, update username & is_global
    if table_id and table_id in game_rooms and player_id in game_rooms[table_id]["players"]:
        username = game_rooms[table_id]["players"][player_id]["username"]
        is_global = False

    chat_data = {
        "playerId": player_id,
        "username": username,
        "message": message,
        "isglobal": is_global,  # all lowercase to match React check OR
        "isGlobal": is_global,
    }

    if table_id:
        # Room chat: emit only to that room
        print(f"Sending chat to room: {table_id}")
        emit("chat_message", chat_data, room=table_id)
    else:
        # Lobby/global chat: broadcast to all connected clients
        print("Sending global chat message")
        emit("chat_message", chat_data, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=port)
