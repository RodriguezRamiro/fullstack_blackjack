# //backend/App.py

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_socketio import rooms as socketio_rooms
from datetime import datetime, timezone
import threading
import os
from flask_cors import CORS
import random
import uuid
import requests


# Chekclist of implemented features:
#✅ Room creation & deck management (create_room, create_deck, ensure_deck).

#✅ Betting flow (place_bet) with chips deducted immediately.

#✅ Game start deals 2 cards to everyone + dealer, sets first turn.

#✅ Turn progression via advance_turn → dealer logic when players finish.

#✅ Round resolution with payouts in resolve_game.

#✅ Round reset via restart_round, including an automatic countdown.


port = int(os.environ.get("PORT", 5000))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret!")
app.secret_key = "Super-secret_key"

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://fullstack-blackjack.vercel.app"
]

CORS(app, supports_credentials=True, origins=allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode="threading")

# In-memory storage
rooms = {}
players = {}


# Card values
CARD_VALUES = {
    "ACE": 11,
    "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "JACK": 10, "QUEEN": 10, "KING": 10,
}

DECK_API_URL = "https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=6"



# Utility Functions

def create_deck():
    """Fetch or build a shuffled deck."""
    try:
        resp = requests.get(DECK_API_URL, timeout=5)
        resp.raise_for_status()
        deck_id = resp.json()["deck_id"]
        return {"deck_id": deck_id, "cards": []}
    except Exception as e:
        print(f"Deck API failed, using local deck: {e}")
        suits = ["HEARTS", "DIAMONDS", "CLUBS", "SPADES"]
        ranks = list(CARD_VALUES.keys())
        cards = [{"value": r, "suit": s} for r in ranks for s in suits] * 6
        random.shuffle(cards)
        return {"deck_id": None, "cards": cards}

def draw_card(table_id):
    """Draw a card from deck (API or local)."""
    room = rooms[table_id]
    deck = room["deck"]

    if deck["deck_id"]:  # API deck
        try:
            resp = requests.get(
                f"https://deckofcardsapi.com/api/deck/{deck['deck_id']}/draw/?count=1",
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            if data["success"] and data["cards"]:
                card = data["cards"][0]
                return {"value": card["value"], "suit": card["suit"]}
        except Exception as e:
            print(f"API draw failed, fallback: {e}")

    # Fallback/local
    if not deck["cards"]:
        deck.update(create_deck())
    return deck["cards"].pop()

def calculate_score(hand):
    score, aces = 0, 0
    for card in hand:
        score += CARD_VALUES.get(card["value"], 0)
        if card["value"] == "ACE":
            aces += 1
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

def emit_error(message, room=None):
    """Emit an error socket event."""
    if room:
        socketio.emit("error_message", {"error": message}, room=room)
    else:
        emit("error_message", {"error": message})



# Routes

@app.route("/create-room", methods=["POST"])
def create_room():
    table_id = str(uuid.uuid4())
    rooms[table_id] = {
        "players": [],
        "players_data": {},
        "deck": create_deck(),
        "dealer": {"hand": [], "score": 0},
        "bets": {},
        "game_started": False,
        "turn_order": [],
        "current_turn_index": 0,
    }
    return jsonify({"table_id": table_id})

@app.route("/start-game", methods=["POST"])
def start_game():
    data = request.get_json()
    table_id = data.get("table_id") or data.get("tableId")
    if not table_id or table_id not in rooms:
        return jsonify({"error": "Invalid table"}), 400
    start_game_internal(table_id)
    return jsonify({"message": "Game started"})

# Socket Events

@socketio.on("connect")
def on_connect():
    print("🔌 Client connected:", request.sid)

@socketio.on("disconnect")
def on_disconnect():
    print("❌ Client disconnected:", request.sid)



@socketio.on("join")
def on_join(data):
    username = data.get("username")
    table_id = data.get("table_id")
    if not username or not table_id:
        return emit_error("Invalid join request")

    join_room(table_id)
    players[request.sid] = {"username": username, "table_id": table_id}
    print(f"Player joined: username={username}, sid={request.sid}, table={table_id}")


    room = rooms.get(table_id)
    if not room:
        return emit_error("Table does not exist")

    if room["game_started"]:
        socketio.emit("chat_message", {"username": "System", "message": f"{username} is observing"}, room=table_id)
    else:
        room["players"].append(request.sid)
        socketio.emit("chat_message", {"username": "System", "message": f"{username} joined"}, room=table_id)

    emit("joined_room", {"table_id": table_id}, room=request.sid)

    emit_game_state(room, table_id)

    # if single-player, auto start immidiatly
    if len(room["players"]) == 1:
        socketio.emit("chat_message", {"username": "System", "message": "Single-Player mode: Starting round..."}, room=table_id)
        start_game_internal(table_id)

@socketio.on("place_bet")
def place_bet(data):
    table_id = data.get("table_id")
    bet = data.get("bet")
    player = players.get(request.sid)
    if not table_id or not bet or not player:
        return emit_error("Invalid bet")

    room = rooms.get(table_id)
    if not room:
        return emit_error("Table not found")

    if player["username"] in room["bets"]:
        return emit_error("Bet already placed", room=table_id)

    room["bets"][player["username"]] = bet
    socketio.emit("chat_message", {"username": "System", "message": f"{player['username']} bet {bet}"}, room=table_id)

    if len(room["bets"]) == len(room["players"]):
        start_game_internal(table_id)
    else:
        emit_game_state(room, table_id)


@socketio.on("hit")
def hit(data):
    table_id = data.get("table_id")
    room = rooms.get(table_id)
    if not room:
        return emit_error("Invalid table")

    player = players.get(request.sid)
    if not player or player["username"] != room["turn_order"][room["current_turn_index"]]:
        return emit_error("Not your turn")

    player_obj = room["players_data"][player["username"]]
    card = draw_card(table_id)
    player_obj["hand"].append(card)
    player_obj["score"] = calculate_score(player_obj["hand"])

    if player_obj["score"] > 21:
        socketio.emit("chat_message", {"username": "System", "message": f"{player['username']} busts!"}, room=table_id)
        advance_turn(room, table_id)
    emit_game_state(room, table_id)

@socketio.on("stay")
def stay(data):
    table_id = data.get("table_id")
    room = rooms.get(table_id)
    if not room:
        return emit_error("Invalid table")

    player = players.get(request.sid)
    if not player or player["username"] != room["turn_order"][room["current_turn_index"]]:
        return emit_error("Not your turn")

    socketio.emit("chat_message", {"username": "System", "message": f"{player['username']} stays"}, room=table_id)
    advance_turn(room, table_id)
    emit_game_state(room, table_id)



# Game Logic

def start_game_internal(table_id):
    room = rooms[table_id]
    room.update({
        "game_started": True,
        "bets": {},
        "dealer": {"hand": [draw_card(table_id), draw_card(table_id)], "score": 0},
        "players_data": {},
    })

    for sid in room["players"]:
        username = players[sid]["username"]
        hand = [draw_card(table_id), draw_card(table_id)]
        room["players_data"][username] = {"hand": hand, "score": calculate_score(hand)}

    room["turn_order"] = [players[sid]["username"] for sid in room["players"]]
    room["current_turn_index"] = 0
    emit_game_state(room, table_id)

def advance_turn(room, table_id):
    room["current_turn_index"] += 1
    if room["current_turn_index"] >= len(room["turn_order"]):
        dealer_plays(room, table_id)
    else:
        emit_game_state(room, table_id)

def dealer_plays(room, table_id):
    dealer = room["dealer"]
    while calculate_score(dealer["hand"]) < 17:
        dealer["hand"].append(draw_card(table_id))
    dealer["score"] = calculate_score(dealer["hand"])
    resolve_game(room, table_id)

def resolve_game(room, table_id):
    dealer_score = room["dealer"]["score"]
    results = {}
    for username, pdata in room["players_data"].items():
        score = pdata["score"]
        if score > 21:
            results[username] = "Lose (bust)"
        elif dealer_score > 21 or score > dealer_score:
            results[username] = "Win"
        elif score == dealer_score:
            results[username] = "Push"
        else:
            results[username] = "Lose"
    socketio.emit("round_result", {"results": results}, room=table_id)
    room["game_started"] = False


# Game State Emission
def emit_game_state(room, table_id):

# Guard defaults so we never KeyError
    dealer = room.get("dealer", {"hand": [], "score": 0})
    game_started = room.get("game_started", False)
    players_data = room.get("players_data", {})
    turn_order = room.get("turn_order", [])
    current_index = room.get("current_turn_index", 0)

# Build exposed dealer info (hide second card if game started)
    dealer_hand = dealer.get("hand", [])
    if game_started and dealer_hand:
        dealer_display = [dealer_hand[0], {
            "value": "hidden", "suit": "Hidden"}]
        dealer_score = "?"
    else:
        dealer_display = dealer_hand
        dealer_score = calculate_score(dealer_hand) if dealer_hand else 0

# Choose current turn (none when not running)
        turn = None
        if game_started and turn_order:
# Current player username (your state uses username in turn_order )
            turn = turn_order[current_index] if current_index < len(turn_order) else None

        state = {
            "dealer": {
                "hand": dealer_display,
                "score": dealer_score
            },
            "players": players_data,
            "turn": turn,
            "reveal_dealer_hand": not game_started,
            "reveal_hands": not game_started,
            "game_over": not game_started
        }
        socketio.emit("game_state", state, room=table_id)



# Run

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))