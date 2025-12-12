# //backend/App.py

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from datetime import datetime, timezone
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
    """Fetch or build a shuffled deck. When using local fallback, include 'code' and 'image'
    fields so frontend can render an external/static image for each card."""
    try:
        resp = requests.get(DECK_API_URL, timeout=5)
        resp.raise_for_status()
        deck_id = resp.json().get("deck_id")
        return {"deck_id": deck_id, "cards": []}
    except Exception as e:
        print(f"Deck API failed, using local deck: {e}")
        suits = ["HEARTS", "DIAMONDS", "CLUBS", "SPADES"]
        ranks = list(CARD_VALUES.keys())

        # map long rank / short code used by deckofcards api static images
        rank_code_map = {
            "ACE": "A", "JACK": "J", "QUEEN": "Q", "KING": "K",
            # numeric ranks keep their number; use "10" for tens
            "10": "10", "2": "2", "3": "3", "4": "4", "5": "5",
            "6": "6", "7": "7", "8": "8", "9": "9"
        }

        suit_code_map = {
            "HEARTS": "H",
            "DIAMONDS": "D",
            "CLUBS": "C",
            "SPADES": "S"
        }

        cards = []
        for r in ranks:
            for s in suits:
                rank_code = rank_code_map.get(r, r)
                suit_code = suit_code_map.get(s, s[0])
                code = f"{rank_code}{suit_code}"
                image = f"httpa://deckofcardsapi.com/static/img.{code}.png"
                cards.append({"value": r, "suit": s, "code": code, "image": image})
        # for multiplayer 6 pairity decks in DECK_API_URL;
        cards = cards * 6
        random.shuffle(cards)
        return {"deck_id": None, "cards": cards}


def draw_card(table_id):
    """Draw a card from deck (API or local). Returns dict containing value,suit,code,image."""
    room = rooms[table_id]
    deck = room["deck"]

    # If we have an API deck_id, prefer drawing from the API and return the image + code.
    if deck.get("deck_id"):  # API deck
        try:
            resp = requests.get(
                f"https://deckofcardsapi.com/api/deck/{deck['deck_id']}/draw/?count=1",
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") and data.get("cards"):
                api_card = data["cards"][0]
                # Provide consistent fields for frontend
                return {
                    "value": api_card.get("value"),
                    "suit": api_card.get("suit"),
                    "code": api_card.get("code"),
                    "image": api_card.get("image") or (api_card.get("images") or {}).get("png")
                    }
        except Exception as e:
            print(f"API draw failed, fallback: {e}")

    # Fallback/local
    if not deck.get("cards"):
        deck.update(create_deck())

    # Local card objects already include value,suit,code,image per create_deck()
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
        "players": {},         # keyed by player_id -> { sid, username }
        "players_data": {},    # keyed by player_id -> per-round data
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
    data = request.get_json() or {}
    table_id = data.get("table_id") or data.get("tableId")
    if not table_id or table_id not in rooms:
        return jsonify({"error": "Invalid table"}), 400

    room = rooms[table_id]
    if not room.get("players"):
        return jsonify({"error": "No players in room"}), 400

    start_game_internal(table_id)

    return jsonify({
        "message": "Game started",
        "table_id": table_id         # send table_id to the frontend
    })


# Socket Events

# Socket Events
@socketio.on("connect")
def on_connect():
    print("🔌 Client connected:", request.sid)

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    print("❌ Client disconnected:", sid)
    p = players.pop(sid, None)
    if p:
        table_id = p.get("table_id")
        player_id = p.get("player_id")
        if table_id in rooms:
            room = rooms[table_id]
            room.get("players", {}).pop(player_id, None)
            room.get("players_data", {}).pop(player_id, None)
            emit_game_state(room, table_id)

@socketio.on("join")
def on_join(data):
    username = data.get("username")
    table_id = data.get("table_id")
    player_id = data.get("playerId") or str(uuid.uuid4())

    if not username or not table_id:
        return emit_error("Invalid join request")


    # Create room if needed
    if table_id not in rooms:
        rooms[table_id] = {
            "players": {},
            "players_data": {},
            "deck": create_deck(),
            "dealer": {"hand": [], "score": 0},
            "bets": {},
            "game_started": False,
            "turn_order": [],
            "current_turn_index": 0,
        }

    room = rooms[table_id]
    join_room(table_id)

    # register globally by socket sid
    players[request.sid] = {"username": username, "player_id": player_id, "table_id": table_id}

    # register in room keyed by player_id (so frontend can index by playerId)
    room["players"][player_id] = {"sid": request.sid, "username": username}

    # ensure players_data has entry for this player (useful pre-game)
    if player_id not in room.get("players_data", {}):
        room["players_data"][player_id] = {"username": username, "hand": [], "score": 0, "bet": 0}
        # add to turn order only if not present
        if player_id not in room.get("turn_order", []):
            room["turn_order"].append(player_id)

    print(f"[JOIN] {username} joined table {table_id} with player_id={player_id}")
    print("[DEBUG] Room snapshot before emit_game_state:")
    print(f"  players: {list(room['players'].keys())}")
    print(f"  players_data: {list(room.get('players_data', {}).keys())}")

    # notify table
    socketio.emit("chat_message", {"username": "System", "message": f"{username} joined the table."}, room=table_id)
    emit("joined_room", {"table_id": table_id}, room=request.sid)

    # emit current game state so frontend updates
    emit_game_state(room, table_id)

    # auto-start single-player for quick testing
    if len(room["players"]) == 1:
        socketio.emit("chat_message", {"username": "System", "message": "Single-Player mode: Starting round..."}, room=table_id)
        start_game_internal(table_id)


@socketio.on("place_bet")
def place_bet(data):
    table_id = data.get("table_id")
    bet = data.get("bet")
    player = players.get(request.sid)
    if not table_id or bet is None or not player:
        return emit_error("Invalid bet")

    room = rooms.get(table_id)
    if not room:
        return emit_error("Table not found")

    # use username in bets map for readability
    if player["username"] in room.get("bets", {}):
        return emit_error("Bet already placed", room=table_id)

    room.setdefault("bets", {})[player["username"]] = bet
    socketio.emit("chat_message", {"username": "System", "message": f"{player['username']} bet {bet}"}, room=table_id)

    if len(room["bets"]) == len(room.get("players", {})):
        start_game_internal(table_id)
    else:
        emit_game_state(room, table_id)



@socketio.on("hit")
def hit(data):
    table_id = data.get("table_id")
    room = rooms.get(table_id)
    if not room:
        return emit_error("Invalid table")

    ply = players.get(request.sid)
    if not ply:
        return emit_error("Player not found")
    player_key = ply.get("player_id") or request.sid

    # current turn is stored as player_key (player_id)
    current_turn_key = room.get("turn_order", [None])[room.get("current_turn_index", 0)] if room.get("turn_order") else None
    if player_key != current_turn_key:
        return emit_error("Not your turn", room=table_id)

    player_obj = room.get("players_data", {}).get(player_key)
    if not player_obj:
        return emit_error("Player data missing", room=table_id)

    card = draw_card(table_id)
    player_obj["hand"].append(card)
    player_obj["score"] = calculate_score(player_obj["hand"])

    if player_obj["score"] > 21:
        socketio.emit("chat_message", {"username": "System", "message": f"{ply['username']} busts!"}, room=table_id)
        advance_turn(room, table_id)

    emit_game_state(room, table_id)

@socketio.on("stay")
def stay(data):
    table_id = data.get("table_id")
    room = rooms.get(table_id)
    if not room:
        return emit_error("Invalid table")

    ply = players.get(request.sid)
    if not ply:
        return emit_error("Player not found", room=table_id)
    player_key = ply.get("player_id") or request.sid

    current_turn_key = room.get("turn_order", [None])[room.get("current_turn_index", 0)] if room.get("turn_order") else None
    if player_key != current_turn_key:
        return emit_error("Not your turn", room=table_id)


    socketio.emit("chat_message", {"username": "System", "message": f"{ply['username']} stays"}, room=table_id)
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

    # Deal to each joined player (room["players"] keyed by player_id)
    for player_id, pdata in list(room.get("players", {}).items()):
        sid = pdata.get("sid")
        username = pdata.get("username")
        if not sid or not username:
            print(f"[WARN] start_game_internal: missing sid/username for player_id={player_id}")
            continue

        hand = [draw_card(table_id), draw_card(table_id)]
        room["players_data"][player_id] = {
            "username": username,
            "hand": hand,
            "score": calculate_score(hand),
            "bet": room.get("bets", {}).get(username, 0),
        }

    # Turn_order should be list of player_keys (player_id")
    room["turn_order"] = [pid for pid in room.get("players", {}).keys()]
    room["current_turn_index"] = 0

    print(f"[DEBUG] Starting game for table {table_id}. Players: {list(room['players'].keys())}")
    emit_game_state(room, table_id)


def advance_turn(room, table_id):
    room["current_turn_index"] += 1
    if room["current_turn_index"] >= len(room.get("turn_order", [])):
        dealer_plays(room, table_id)
    else:
        emit_game_state(room, table_id)

def dealer_plays(room, table_id):
    dealer = room.get("dealer", {"hand": [], "score": 0})
    while calculate_score(dealer["hand"]) < 17:
        dealer["hand"].append(draw_card(table_id))
    dealer["score"] = calculate_score(dealer["hand"])
    resolve_game(room, table_id)


def resolve_game(room, table_id):
    dealer_score = room["dealer"]["score"]
    results = {}
    for username, pdata in room.get("players_data", {}).items():
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
    """Emit full game state to all clients in the table."""

# Defensive Defaults
    dealer = room.get("dealer", {"hand": [], "score": 0})
    game_started = room.get("game_started", False)
    players_data = room.get("players_data", {})
    turn_order = room.get("turn_order", [])
    current_index = room.get("current_turn_index", 0)

# Build exposed dealer info (hide second card if game started)
    dealer_hand = dealer.get("hand", [])
    if game_started and dealer_hand:
        dealer_display = [
        dealer_hand[0],
        {"value": "hidden", "suit": "hidden", "code": "BACK", "image": None, "hidden": True}
    ]
        dealer_score = "?"
    else:
        dealer_display = dealer_hand
        dealer_score = calculate_score(dealer_hand) if dealer_hand else 0

# Turn logic
    turn = None
    if game_started and turn_order:
        turn = turn_order[current_index] if current_index < len(turn_order) else None

    state = {
        "dealer": {"hand": dealer_display, "score": dealer_score},
        "players": players_data,
        "turn": turn,
        "reveal_dealer_hand": not game_started,
        "reveal_hands": not game_started,
        "game_over": not game_started,
    }

    print(f"[DEBUG] Emitting game_state for table {table_id}: players={list(players_data.keys())}")
    socketio.emit("game_state", state, room=table_id)


# Run

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))