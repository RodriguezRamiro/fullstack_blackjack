#/backend/app.py

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit, rooms
from datetime import datetime
import os
from flask_cors import CORS
import random
import uuid
import requests


port = int(os.environ.get("PORT", 5000))

app = Flask(__name__)
app.secret_key = "Super-secret_key"

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://fullstack-blackjack.vercel.app"
]

CORS(app, supports_credentials=True, origins=allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode="threading")

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
            print("Fetched card:", card)
    ]

def calculate_score(hand):
    print(f"Calculating score for hand: {hand}")

    values = {
        'A': 11, '2': 2, '3': 3, '4': 4, '5': 5,
        '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10
    }

    score = 0
    aces = 0

    for card in hand:
        print(f" Card details: {card}")
        rank = card.get('rank')

        # Normalize bad rank values (e.g., some APIs may return '0' for '10')
        if rank == '0':
            rank = '10'

        if not rank:
            print(f"[Error] Malformed card object: {card}")
            continue

        if rank in values:
            score += values[rank]
            if rank == 'A':
                aces += 1
        else:
            print(f"[WARNING] Unknown rank value: {rank}")

    # Adjust for Aces if score is over 21
    while score > 21 and aces:
        score -= 10
        aces -= 1

    return score


@app.route("/create-room", methods=["POST"])
def create_room():
    table_id = str(uuid.uuid4())
    if table_id in game_rooms:
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

    print(f"recieved start-game request: tableId={table_id}, playerId={player_id}")

    if not table_id or not player_id:
        print("Missing tableId or playerId in request")
        return jsonify({"error": "Missing tableId or playerId."}), 404

    if table_id not in game_rooms:
        print(f"Room {table_id} does not exist in game_rooms")
        print(f"Current rooms: {list(game_rooms.keys())}")
        return jsonify({"error": "Room does not exist."}), 400

    room = game_rooms[table_id]

    print(f"players in room: {list(room['players'].keys())}")
    for pid, player in room["players"].items():
        print(f"Player {pid} bet: {player.get('bet')}")

    # Only require valid bets if there are 2 or more players
    if len(room["players"]) >= 2:
        if any("bet" not in p or p["bet"] <=0 for p in room["players"].values()):
            print("Not all players have placed a valid bet")
            return jsonify({"error": "All players must playce a valid bet before starting."}), 400
    else:
        print("only one player in room - skipping bet validation")
        #Set default bet zero for constistancy
        for p in room["players"].values():
            p.setdefault("bet", 0)
            p.setdefault("chips", 1000)

    if player_id not in room["players"]:
        print(f"Player {player_id} not found in room players")
        return jsonify({"error": "Player not found in room."}), 400

    room["started"] = True
    room["game_over"] = False

    needed_cards = len(room["players"]) * 2 + 2
    if len(room["deck"]) < needed_cards:
        room["deck"] += create_deck()

    random.shuffle(room["deck"])

    print("Initial cards being used:")
    for pid in room["players"]:
        # Draw cards to check them before score calculation
        hand = [room["deck"].pop(), room["deck"].pop()]
        room["players"][pid].update({
            "hand": hand,
            "score": calculate_score(hand),
            "status": "playing"
        })

    room["dealer"] = {
        "hand": [room["deck"].pop(), room["deck"].pop()],
        "score": 0
    }
    try:
        room["dealer"]["score"] = calculate_score(room["dealer"]["hand"])
    except Exception as e:
        print(f"[ERROR] Failed to calculate dealer score: {e}")
        return jsonify({"error": "Failed to calculate dealer score."}), 500

    emit_game_state(room, table_id)

    return jsonify({"message": "Game started.", "tableId": table_id})

def sid_to_pid(room, sid):
    for pid, pdata in room.get("players", {}).items():
        if pdata.get("sid") == sid:
            return pid
    return None

def get_public_game_state(room):
    return {
        "players": {
            pid: {
                "username": pdata["username"],
                "hand": ["Hidden"] * len(pdata["hand"]),
                "score": None,
                "status": pdata["status"]
            }
            for pid, pdata in room.get("players", {}).items()
        },
        "dealer": public_dealer_hand(room.get("dealer", {}), room.get("game_over", False)),
        "deckCount": len(room.get("deck", [])),
        "game_over": room.get("game_over", False)
    }

@socketio.on('place_bet')
def handle_place_bet(data):
    sid = request.sid
    table_id = data.get('tableId')
    player_id = data.get('playerId')
    bet = data.get('bet')

    if not table_id or not player_id or bet is None:
        emit('error', {'message': 'Invalid bet request'}, to=sid)
        return

    room = game_rooms.get(table_id)
    if not room:
        emit('error', {'message': 'Room not found'}, to=sid)
        return

    player = room['players'].get(player_id)
    if not player:
        emit('error', {'message': 'Player not found'}, to=sid)
        return

    # Initialize chips if not set
    if 'chips' not in player:
        player['chips'] = 1000

    # Validate bet amount
    if bet < 1:
        emit('error', {'message': 'Bet must be at least 1'}, to=sid)
        return
    if bet > player['chips']:
        emit('error', {'message': f'Not enough chips. You have {player["chips"]}.'}, to=sid)
        return

    # Apply bet
    player['bet'] = bet
    player['chips'] -= bet
    print(f"Player {player_id} placed bet ${bet} at table {table_id}. Remaining chips: {player['chips']}")

    # Emit private game state to this player
    emit("game_state", get_private_game_state(room, player_id), to=sid)

    # Emit public game state to all others in room
    emit("game_state", get_public_game_state(room), room=table_id, skip_sid=sid)

    # Notify bet placed publicly
    emit('bet_placed', {
        'tableId': table_id,
        'playerId': player_id,
        'bet': bet,
        'chips': player['chips']
    }, room=table_id)

def can_place_bet(room_id):
    return len(rooms.get(room_id, [])) > 1

def get_private_game_state(room, player_id):
    private_players = {}
    for pid, pdata in room["players"].items():
        if pid == player_id:
            private_players[pid] = pdata
        else:
            private_players[pid] = {
                "username": pdata["username"],
                "hand": ["Hidden"] * len(pdata["hand"]),
                "score": None,
                "status": pdata["status"]
            }
    return {
        "players": private_players,
        "dealer": room["dealer"],
        "deckCount": len(room["deck"]),
        "game_over": room["game_over"]
    }

@socketio.on("join")
def handle_join(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    username = data.get("username")

    if not all([table_id, player_id, username]):
        print("Join failed: missing data", data)
        return

    print(f" Before Join: {list(game_rooms.get(table_id, {}).get('players', {}).keys())}")

    if table_id not in game_rooms:
        emit("room_not_found", {}, to=request.sid)
        return

    room = game_rooms[table_id]
    if player_id not in room["players"]:
        room["players"][player_id] = {
            "username": username,
            "hand": [],
            "score": 0,
            "status": "waiting",
            "chips": 1000,
            "sid": request.sid
        }
    else:
        room["players"][player_id]["sid"] = request.sid

    join_room(table_id)

    print(f"[JOIN] player_id={player_id}, sid={request.sid}, table={table_id}, username={username}")
    print(f"After Join: {list(room['players'].keys())}")

    emit("joined_room", {"tableId": table_id}, to=request.sid)


# Emit updated player list (send usernames or player IDs)
    player_list = [p["username"] for p in room["players"].values()]
    emit("players_update", player_list, room=table_id)


    # Leave other rooms except this and private sid room
    current_rooms = rooms(request.sid)
    for r in current_rooms:
        if r != request.sid and r != table_id:
            leave_room(r)


    emit("game_state", {
    "players": {
    pid: pdata for pid, pdata in room["players"].items()
},
    "dealer": room["dealer"],
    "deckCount": len(room["deck"]),
    "game_over": room["game_over"]
}, room=table_id)

@socketio.on("hit")
def handle_hit(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    if table_id not in game_rooms or player_id not in game_rooms[table_id]["players"]:
        emit("error", {"message": "Invalid table or player."}, to=request.sid)
        return

    room = game_rooms[table_id]
    player = room["players"][player_id]

    if player["status"] in ["bust", "stay"]:
        emit("error", {"message": "You cannot hit after staying or busting."}, to=request.sid)
        return

    if len(room["deck"]) == 0:
        new_deck = create_deck()
        room["deck"] += [
            {
                "suit": card.get("suit", ""),
                "rank": card.get("rank") or card.get("value", ""),
                "image": card.get("image", "")
            } for card in new_deck
]
        random.shuffle(room["deck"])

    card = room["deck"].pop()
    player["hand"].append(card)
    player["score"] = calculate_score(player["hand"])

    if player["score"] > 21:
        player["status"] = "bust"

    emit_game_state(room, table_id)

@socketio.on("stay")
def handle_stay(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    if table_id not in game_rooms or player_id not in game_rooms[table_id]["players"]:
        emit("error", {"message": "Invalid table or player."}, to=request.sid)
        return

    room = game_rooms[table_id]
    player = room["players"][player_id]

    if player["status"] in ["bust", "stay"]:
        emit("error", {"message": "You already stayed or busted."}, to=request.sid)
        return

    player["status"] = "stay"

    # If all players done, dealer plays
    if all(p["status"] in ["bust", "stay"] for p in room["players"].values()):
        while room["dealer"]["score"] < 17:
            if len(room["deck"]) == 0:
                new_deck = create_deck()
                room["deck"] += [
                    {
                        "suit": card.get("suit", ""),
                        "rank": card.get("rank") or card.get("value", ""),
                        "image": card.get("image", "")
                    } for card in new_deck
]
                random.shuffle(room["deck"])
            room["dealer"]["hand"].append(room["deck"].pop())
            room["dealer"]["score"] = calculate_score(room["dealer"]["hand"])

        resolve_game(table_id)
    else:
        emit_game_state(room, table_id)

def resolve_game(table_id):
    room = game_rooms[table_id]
    dealer_score = calculate_score(room['dealer']['hand'])
    room['dealer']['score'] = dealer_score

    for player_id, player in room['players'].items():
        bet = player.get('bet', 0)
        player_score = player.get('score', 0)

        # Ensure chips key exists
        player.setdefault("chips", 0)


        if player['status'] == 'bust' or player_score > 21:
            player['result'] = 'lose'
            # chips stay the same
        elif dealer_score > 21 or player_score > dealer_score:
            player['result'] = 'win'
            player['chips'] += bet * 2
        elif player_score == dealer_score:
            player['result'] = 'push'
            player['chips'] += bet
        else:
            player['result'] = 'lose'
            # chips stay the same

        print(f"Player {player_id} result: {player['result']} | Chips: {player['chips']}")

    room['game_over'] = True

    emit('game_over', {
        'players': {
            pid: {
                'result': p['result'],
                'chips': p['chips']
            } for pid, p in room['players'].items()
        },
        'dealer': room['dealer']
    }, room=table_id)

    socketio.emit("game_state", {
        "players": room["players"],
        "dealer": room["dealer"],
        "deckCount": len(room["deck"]),
        "game_over": room["game_over"]
    }, room=table_id)

@socketio.on("leave")
def handle_leave(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    leave_room(table_id)

    if table_id in game_rooms and player_id in game_rooms[table_id]["players"]:
        del game_rooms[table_id]["players"][player_id]

        if not game_rooms[table_id]["players"]:
            del game_rooms[table_id]
        else:
            emit_game_state(game_rooms.get(table_id, {}), table_id)

def emit_game_state(room, table_id, sid=None):
    if not room:
        print(f"[WARNING] emit_game_state called with empty room: {table_id}")
        return
    socketio.emit("game_state", {
        "players": {
            pid: {
                "username": pdata["username"],
                "hand": pdata["hand"],
                "score": pdata["score"],
                "status": pdata["status"]
            } if sid and pdata.get("sid") == sid else {
                "username": pdata["username"],
                "hand": ["Hidden"] * len(pdata["hand"]),
                "score": None,
                "status": pdata["status"]
            }
            for pid, pdata in room.get("players", {}).items()
        },
        "dealer": public_dealer_hand(room.get("dealer", {}), room.get("game_over", False)),
        "deckCount": len(room.get("deck", [])),
        "game_over": room.get("game_over", False)
    }, room=table_id)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"Client {request.sid} disconnected.")

    tables_to_delete = []
    for table_id, room in list(game_rooms.items()):
        to_remove = []
        for player_id, player in list(room["players"].items()):
            if player.get("sid") == sid:
                to_remove.append(player_id)
        for pid in to_remove:
                leave_room(table_id, sid=sid)
                del room["players"][pid]
                print(f"Removed player {pid} from {table_id}")

        #Emit updated player list after removals
        player_list =[p["username"] for p in room["players"].values()]
        emit("players_update", player_list, room=table_id)

        if not room["players"]:
            tables_to_delete.append(table_id)

    for table_id in tables_to_delete:
        print(f"Deleting empty table {table_id}")
        del game_rooms[table_id]

def public_dealer_hand(dealer, game_over):
    print(f"public_dealer_hand called with dealer: {dealer}, game_over: {game_over}")
    if not dealer or "hand" not in dealer or len(dealer["hand"]) == 0:
        print("Dealer hand empty or missing, returning empty")
        #Dealer hand not ready yet, return empty or placeholder
        return {"hand": [], "score": 0}
    if game_over:
        #Show full dealer hand if game over
        return {"hand": dealer["hand"], "score": dealer["score"]}

    else:
        #Show only first card, hide second
        first_card = dealer["hand"][0]
        rank = first_card.get("rank")
        partial_score = 11 if rank == "A" else 10 if rank in ["K", "Q", "J"] else int(rank) if rank.isdigit() else 0
        return {"hand": [first_card, "Hidden"], "score": partial_score}


@socketio.on("chat_message")
def handle_chat_message(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    message = data.get("message")
    username = data.get("username", "Anonymous")

    if not message:
        return

    is_global = True
    if table_id and table_id in game_rooms and player_id in game_rooms[table_id]["players"]:
        username = game_rooms[table_id]["players"][player_id]["username"]
        is_global = False

    chat_data = {
        "playerId": player_id,
        "username": username,
        "message": message,
        "isglobal": is_global,
        "tableId": table_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if table_id:
        emit("chat_message", chat_data, room=table_id)
    else:
        emit("chat_message", chat_data, broadcast=True)

if __name__ == "__main__":
    print("Before socketio.run")
    socketio.run(app, host="0.0.0.0", port=port)
