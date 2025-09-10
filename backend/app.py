# App.py

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


#local deck fallback
def create_deck_local():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
    deck = [{"suit": s, "rank": r, "image": "cardBack", "code": f"{r}{s}"} for s in suits for r in ranks]
    random.shuffle(deck)
    return deck


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

    try:
        response = requests.get(
            "https://deckofcardsapi.com/api/deck/new/draw/?count=52",
            timeout=3
        )
        response.raise_for_status()
        data = response.json()
        cards = data.get("cards") or []
        if not cards:
            raise Exception("No cards found in API response.")
        return [
            {
                "suit": suits_map.get(card.get("suit"), card.get("suit")),
                "rank": rank_map.get(card.get("value"), card.get("value")),
                "image": card.get("image"),
                "code": card.get("code")
            }
            for card in cards
        ]
    except Exception as e:
        print(f"[DECK] external API failed ({e}), falling back to local deck.")
        return create_deck_local()


def calculate_score(hand):
    # print(f"Calculating score for hand: {hand}") # Uncomment for debugging

    values = {
        'A': 11, '2': 2, '3': 3, '4': 4, '5': 5,
        '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10
    }

    score = 0
    aces = 0

    for card in hand:
        # print(f" Card details: {card}") # Uncomment for debugging
        rank = card.get('rank')

        # Normalize bad rank values (e.g., some APIs may return '0' for '10') - though API returns "10"
        if rank == '0':
            rank = '10'

        if not rank:
            print(f"[Error] Malformed card object (missing rank): {card}")
            continue

        if rank in values:
            score += values[rank]
            if rank == 'A':
                aces += 1
        elif rank.isdigit(): # Catches "10" if it wasn't in values, or other unexpected numbers
            score += int(rank)
        else:
            print(f"[WARNING] Unknown rank value encountered during score calculation: {rank} for card {card}")

    # Adjust for Aces if score is over 21
    while score > 21 and aces:
        score -= 10
        aces -= 1

    return score


@app.route("/create-room", methods=["POST"])
def create_room():
    table_id = str(uuid.uuid4())
    # You might want to add a check for extremely rare UUID collisions,
    # but for practical purposes, it's highly unlikely.
    if table_id in game_rooms:
         # This case should be virtually impossible with uuid4(), but good to have
        print(f"UUID collision for table_id: {table_id}. Retrying or reporting.")
        return jsonify({"error": "Failed to create unique room ID. Please try again."}), 500

    try:
        new_deck = create_deck()
    except Exception as e:
        print(f"Error creating deck for new room: {e}")
        return jsonify({"error": "Failed to initialize game room. Deck creation failed."}), 500


    game_rooms[table_id] = {
        "players": {},
        "dealer": {"hand": [], "score": 0},
        "deck": new_deck, # Initialize with a fresh deck
        "started": False,
        "game_over": False,
        "current_turn": None # To manage player turns, useful for multiplayer
    }

    print(f"Room {table_id} created.")
    return jsonify({"message": "Room created", "tableId": table_id})

# Deck management
def ensure_deck(room):
    """Make sure the rooms'deck isnt empty, replenish if needed."""
    if not room["deck"]:
        room["deck"].extend(create_deck())
        random.shuffle(room["deck"])

# Consistent Error Helper
def emit_error(message, sid=None, room=None):
    """ Emit Errors consistently to sid or room."""
    if sid:
        socketio.emit("error", {"message": message}, to=sid)
    elif room:
        socketio.emit("error", {"message": message}, room=room)
    print(f"[ERROR] {message}")


@app.route("/start-game", methods=["POST"])
def start_game():
    data = request.get_json()
    table_id = data.get("tableId")
    player_id = data.get("playerId") # The player initiating the start

    print(f"Received start-game request: tableId={table_id}, playerId={player_id}")

    if not table_id or not player_id:
        print("Missing tableId or playerId in request for start_game")
        return jsonify({"error": "Missing tableId or playerId."}), 400

    room = game_rooms.get(table_id)
    if not room:
        print(f"Room {table_id} does not exist in game_rooms")
        print(f"Current rooms: {list(game_rooms.keys())}")
        return jsonify({"error": "Room does not exist."}), 404

    # Ensure the initiating player is in the room
    if player_id not in room["players"]:
        print(f"Player {player_id} not found in room players {table_id}")
        return jsonify({"error": "Player not found in room."}), 400

    # Allow game start if a previous game was already started but it has ended (game_over = True)
    if room["started"] and not room.get("game_over", False):
        print(f"Game in room {table_id} already started and not over.")
        return jsonify({"error": "Game already started."}), 400

    # Betting logic adjustment for playing without betting when alone
    active_players_count = len(room["players"])

    if active_players_count >= 2:
        # If 2 or more players, all must have placed a valid bet
        if any(p.get("bet", 0) <= 0 for p in room["players"].values()):
            print("Not all players have placed a valid bet.")
            return jsonify({"error": "All players must place a valid bet before starting."}), 400
    else: # Only one player in the room
        print(f"Only one player ({player_id}) in room {table_id} - skipping strict bet validation.")
        # Ensure 'bet' and 'chips' keys are initialized for consistency
        # Player is allowed to play with a 0 bet if they are alone and haven't bet.
        for p in room["players"].values():
            p.setdefault("bet", 0)
            p.setdefault("chips", 1000) # Initialize chips if not already present

    room["started"] = True              # Game is now running
    room["game_over"] = False           # Not over yet
    room["current_turn"] = None         # Will be set after dealing

    # Reset hands and scores for all players and dealer
    for pid in room["players"]:
        room["players"][pid].update({
            "hand": [],
            "score": 0,
            "status": "playing"
        })
    room["dealer"] = {"hand": [], "score": 0}

    # Ensure enough cards in the deck, replenish if necessary
    needed_cards = active_players_count * 2 + 2 # 2 for each player, 2 for dealer
    if len(room["deck"]) < needed_cards:
        print(f"Deck low on cards ({len(room['deck'])}), replenishing for room {table_id}.")
        try:
            room["deck"].extend(create_deck())
        except Exception as e:
            print(f"Error replenishing deck for room {table_id}: {e}")
            return jsonify({"error": "Failed to replenish deck."}), 500
        random.shuffle(room["deck"]) # Shuffle only after extending

    random.shuffle(room["deck"]) # Always shuffle at start of game

    # Deal initial cards
    print("Dealing initial cards:")
    for pid, player_data in room["players"].items():
        try:
            player_hand = [room["deck"].pop(), room["deck"].pop()]
            player_score = calculate_score(player_hand)
            player_data.update({
                "hand": player_hand,
                "score": player_score,
                "status": "playing" # Reset status for new game
            })
            print(f"Player {pid} dealt: {player_hand}, score: {player_score}")
        except IndexError:
            print(f"[ERROR] Deck ran out of cards while dealing to player {pid} in room {table_id}.")
            return jsonify({"error": "Deck ran out of cards during initial deal."}), 500


    try:
        dealer_hand = [room["deck"].pop(), room["deck"].pop()]
        room["dealer_hidden_card"] = dealer_hand[1]
        room["dealer"] = {
            "hand": [dealer_hand[0]],
            "score": calculate_score([dealer_hand[0]]) # Calculate full score for backend, public_dealer_hand hides one.
        }
        print(f"Dealer dealt: {dealer_hand}, score: {room['dealer']['score']}")
    except IndexError:
        print(f"[ERROR] Deck ran out of cards while dealing to dealer in room {table_id}.")
        return jsonify({"error": "Deck ran out of cards during initial deal (dealer)."}), 500
    except Exception as e:
        print(f"[ERROR] Failed to calculate dealer score after initial deal: {e}")
        return jsonify({"error": "Failed to calculate dealer score."}), 500

    # Set the first player's turn
    if room["players"]:
        room["current_turn"] = list(room["players"].keys())[0] # First player in the dict
        print(f"Initial turn set to {room['current_turn']} in room {table_id}")
    emit_game_state(room, table_id)

    print(f"Game started for table {table_id}.")
    return jsonify({"message": "Game started.", "tableId": table_id})

def sid_to_pid(room, sid):
    for pid, pdata in room.get("players", {}).items():
        if pdata.get("sid") == sid:
            return pid
    return None

# This function is not used currently, replaced by explicit logic in emit_game_state
# def get_public_game_state(room):
#     return {
#         "players": {
#             pid: {
#                 "username": pdata["username"],
#                 "hand": ["Hidden"] * len(pdata["hand"]), # This would send string "Hidden"
#                 "score": None,
#                 "status": pdata["status"]
#             }
#             for pid, pdata in room.get("players", {}).items()
#         },
#         "dealer": public_dealer_hand(room.get("dealer", {}), room.get("game_over", False)),
#         "deckCount": len(room.get("deck", [])),
#         "game_over": room.get("game_over", False)
#     }

@socketio.on('place_bet')
def handle_place_bet(data):
    sid = request.sid
    table_id = data.get('tableId')
    player_id = data.get('playerId')
    bet = data.get('bet')

    try:
        bet = int(bet)
    except (TypeError, ValueError):
        socketio.emit('error', {'message': 'Bet must be a number.'}, to=sid)
        return

    if not table_id or not player_id or bet is None:
        socketio.emit('error', {'message': 'Invalid bet request: Missing data'}, to=sid)
        print(f"Invalid bet request from SID {sid}: Missing tableId, playerId, or bet.")
        return

    room = game_rooms.get(table_id)
    if not room:
        socketio.emit('error', {'message': 'Room not found'}, to=sid)
        print(f"Room {table_id} not found for bet request from {player_id}.")
        return

    player = room['players'].get(player_id)
    if not player:
        socketio.emit('error', {'message': 'Player not found in room'}, to=sid)
        print(f"Player {player_id} not found in room {table_id} for bet request.")
        return

    # Initialize chips if not set
    if 'chips' not in player:
        player['chips'] = 1000
        print(f"Player {player_id} chips initialized to 1000.")

    # Validate bet amount
    if bet < 0: # Allow 0 bet for waiting players as intended
        socketio.emit('error', {'message': 'Bet cannot be negative.'}, to=sid)
        print(f"Player {player_id} attempted negative bet: {bet}.")
        return
    if bet > player['chips']:
        socketio.emit('error', {'message': f'Not enough chips. You have {player["chips"]}.'}, to=sid)
        print(f"Player {player_id} attempted bet {bet} but only has {player['chips']} chips.")
        return

    if room["started"]:
        socketio.emit('error', {'message': 'Cannot place bet, game has already started.'}, to=sid)
        print(f"Player {player_id} tried to place bet after game started in room {table_id}.")
        return

    # Apply bet
    player['bet'] = bet
    player['chips'] -= bet # Chips are deducted when bet is placed
    print(f"Player {player_id} placed bet ${bet} at table {table_id}. Remaining chips: {player['chips']}")

    # Emit updated game state to everyone in the room
    # We use emit_game_state which handles private vs. public views
    emit_game_state(room, table_id, sid) # Send private view to sender, public to others

    # Notify bet placed publicly (optional, emit_game_state covers state)
    socketio.emit('bet_placed', {
        'tableId': table_id,
        'playerId': player_id,
        'bet': bet,
        'chips': player['chips'] # Send remaining chips with bet_placed for immediate UI update
    }, room=table_id)


# This function is not used, `emit_game_state` handles private states
# def get_private_game_state(room, player_id):
#     private_players = {}
#     for pid, pdata in room["players"].items():
#         if pid == player_id:
#             private_players[pid] = pdata
#         else:
#             private_players[pid] = {
#                 "username": pdata["username"],
#                 "hand": ["Hidden"] * len(pdata["hand"]),
#                 "score": None,
#                 "status": pdata["status"]
#             }
#     return {
#         "players": private_players,
#         "dealer": room["dealer"],
#         "deckCount": len(room["deck"]),
#         "game_over": room["game_over"]
#     }

@socketio.on("join")
def handle_join(data):
    table_id = data.get("table_id")
    player_id = data.get("player_id")
    username = data.get("username")

    room = game_rooms.get(table_id)
    if not room:
        emit("error", {"message": "Room not found"})
        return

    # Add new player if not in room
    if player_id not in room["players"]:
        new_player = {
            "id": player_id,
            "username": username,
            "hand": [],
            "score": 0,
            "chips": 1000,
            "bet": 0,
            "has_stayed": False,
            "busted": False,
        }
        room["players"][player_id] = new_player
        join_room(table_id)
        emit("joined", {"message": f"{username} joined {table_id}"}, room=table_id)
    else:
        # Reconnect existing player
        join_room(table_id)
        emit("joined", {"message": f"{username} reconnected to {table_id}"}, room=table_id)

    emit_game_state(room, table_id)


# Room and player Validation helper
def get_room_and_player(table_id, player_id, sid, require_turn=False):
    """Helper to fetch room & player with validation. Emits errors if invalid."""
    room = game_rooms.get(table_id)
    if not room:
        socketio.emit("error", {"message": "Room not found"}, to=sid)
        return None, None

    player = room["players"].get(player_id)
    if not player:
        socketio.emit("error", {"message": "Player not found in room"}, to=sid)
        return None, None

    if require_turn and room.get("current_turn") != player_id:
        socketio.emit("error", {"message": "It's not your turn."}, to=sid)
        return None, None

    return room, player

@socketio.on("hit")
def handle_hit(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    # === Validation: Basic request sanity check ===
    if not table_id or not player_id:
        socketio.emit("error", {"message": "Invalid hit request: Missing data."}, to=request.sid)
        print(f"[HIT] Invalid request from SID {request.sid}: Missing tableId or playerId.")
        return

    room = game_rooms.get(table_id)
    if not room or player_id not in room["players"]:
        socketio.emit("error", {"message": "Invalid table or player for hit action."}, to=request.sid)
        print(f"[HIT] Invalid table ({table_id}) or player ({player_id}) from SID {request.sid}.")
        return

    player = room["players"][player_id]

    # === Validation: Turn control ===
    if room.get("current_turn") != player_id:
        socketio.emit("error", {"message": "It's not your turn."}, to=request.sid)
        print(f"[HIT] Player {player_id} tried to hit out of turn in room {table_id}.")
        return

    # === Validation: Status check ===
    if player["status"] in ["bust", "stay"]:
        socketio.emit("error", {"message": "You cannot hit after staying or busting."}, to=request.sid)
        print(f"[HIT] Player {player_id} tried to hit after being {player['status']} in room {table_id}.")
        return

    # === Refill deck if empty ===
    if len(room["deck"]) == 0:
        room["deck"].extend(create_deck())
        random.shuffle(room["deck"])
        print(f"[HIT] Deck empty for room {table_id}, created new deck.")

    # === Deal a single card ===
    try:
        card = room["deck"].pop()
        player["hand"].append(card)
        player["score"] = calculate_score(player["hand"])
        print(f"[HIT] Player {player_id} drew {card['rank']} of {card['suit']}. Score: {player['score']}")
    except IndexError:
        socketio.emit("error", {"message": "Deck ran out of cards."}, to=request.sid)
        print(f"[HIT] Deck ran out for player {player_id} in room {table_id}.")
        return
    except Exception as e:
        socketio.emit("error", {"message": "An error occurred while hitting."}, to=request.sid)
        print(f"[HIT] Error for player {player_id} in room {table_id}: {e}")
        return

    # === Status update ===
    if player["score"] > 21:
        player["status"] = "bust"
        print(f"[HIT] Player {player_id} busted at {player['score']}. Advancing turn.")
        advance_turn(room, table_id)  # Your existing turn advancement
    else:
        # Keep the player in a "playing" state so they can hit again
        player["status"] = "playing"

    # === Emit updated state to all clients ===
    emit_game_state(room, table_id)


@socketio.on("stay")
def handle_stay(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    # === Validation: Basic request sanity check ===
    if not table_id or not player_id:
        socketio.emit("error", {"message": "Invalid stay request: Missing data."}, to=request.sid)
        print(f"[STAY] Invalid request from SID {request.sid}: Missing tableId or playerId.")
        return

    room = game_rooms.get(table_id)
    if not room or player_id not in room["players"]:
        socketio.emit("error", {"message": "Invalid table or player for stay action."}, to=request.sid)
        print(f"[STAY] Invalid table ({table_id}) or player ({player_id}) from SID {request.sid}.")
        return

    player = room["players"][player_id]

    # === Validation: Turn control ===
    if room.get("current_turn") != player_id:
        socketio.emit("error", {"message": "It's not your turn."}, to=request.sid)
        print(f"[STAY] Player {player_id} tried to stay out of turn in room {table_id}.")
        return

    # === Validation: Status check ===
    if player["status"] in ["bust", "stay"]:
        socketio.emit("error", {"message": "You already stayed or busted."}, to=request.sid)
        print(f"[STAY] Player {player_id} tried to stay after being {player['status']} in room {table_id}.")
        return

    # === Update status ===
    player["status"] = "stay"
    print(f"[STAY] Player {player_id} stays with score {player['score']}.")

    # === Advance turn ===
    advance_turn(room, table_id)

    # === Emit updated state to all clients ===
    emit_game_state(room, table_id)



def advance_turn(room, table_id):
    """
    Advances the turn to the next player still marked as 'playing'.
    If no players remain, initiates the dealer's turn.
    """

    player_ids = list(room.get("players", {}).keys())
    if not player_ids:
    # no players: move directly to dealer
        print(f"[TURN] no players in room {table_id}; switching to dealer.")
        room["current_turn"] = "dealer"
        room["reveal_dealer_hand"] = True
        room["reveal_hands"] = True
        emit_game_state(room, table_id)
        socketio.sleep(1.5)
        dealer_plays(room, table_id)
        return

    # Determine the index of the current player (or -1 if invalid)
    current_player_idx = (
        player_ids.index(room.get("current_turn"))
        if room.get("current_turn") in player_ids
        else -1
    )

    next_player_id = None

    # === Find the next active player ===
    for i in range(1, len(player_ids) + 1):
        next_idx = (current_player_idx + i) % len(player_ids)
        candidate_id = player_ids[next_idx]

        if room["players"][candidate_id]["status"] == "playing":
            next_player_id = candidate_id
            break

    # === If a next player is found ===
    if next_player_id:
        room["current_turn"] = next_player_id
        print(f"[TURN] Advanced to player {next_player_id} in room {table_id}.")
        emit_game_state(room, table_id) #Update all clients Immidiatly
        return

    # Always emit state so frontend updates immediately
    print(f"[TUNR] All players  done in too {table_id}. Dealer's Turn.")
    room["current_turn"] = "dealer"
    room["reveal_dealer_hand"] = True
    room["reveal_hands"] = True # also reveal all players

    # Send reveal state to front end immidiatly
    emit_game_state(room, table_id)

    # Short pause before dealer plays so reveal is visible
    socketio.sleep(1.5)

    # Dealer Logic (runs after reveal)
    dealer_plays(room, table_id)
    return



def dealer_plays(room, table_id):
    """
    Handles dealer drawing until 17+, then calls resolve_game to settle bets.
    """
    if not room:
        print(f"[DEALER] Room {table_id} not found.")
        return

    print(f"[DEALER] Dealer plays in {table_id}...")

    # Reveal hidden card if set
    hidden = room.pop("dealer_hidden_card", None)
    if hidden:
        room["dealer"]["hand"].append(hidden)

    # Recalculate dealer score after reveal
    room["dealer"]["score"] = calculate_score(room["dealer"]["hand"])

    # Dealer must hit until reaching 17 or more
    while room["dealer"]["score"] < 17:
        card = room["deck"].pop() if room["deck"] else None
        if not card:
            print(f"[ERROR] Dealer could not draw card for {table_id}")
            break
        room["dealer"]["hand"].append(card)
        room["dealer"]["score"] = calculate_score(room["dealer"]["hand"])

    emit_game_state(room, table_id)  # Reveal dealer hand
    resolve_game(table_id)




@socketio.on("restart_round")
def restart_round(table_id, delay=5):
    """
    Resets the room state and automatically starts a new betting round
    after a delay (default 5 seconds).
    """
    room = game_rooms.get(table_id)
    if not room:
        return

    # Reset state...
    room.update({
        "dealer": {"hand": [], "score": 0},
        "dealer_hidden_card": None,
        "current_turn": None,
        "round_over": False,
        "game_over": False,
        "started": False,
        "results": {}
    })

    for pdata in room["players"].values():
        pdata.update({"hand": [], "score": 0, "bet": 0, "has_stayed": False, "busted": False})

    # Notify players new round is coming
    emit("message", {
        "message": f"Next round starting in {delay} seconds..."
    }, room=table_id)

    # Emit current clean state (so UI resets immediately)
    emit_game_state(room, table_id)

    # After delay, open betting
    def open_betting(table_id, delay):
        socketio.sleep(delay)
        emit("message", {"message": "Place your bets!"}, room=table_id)
        emit_game_state(room, table_id)

    socketio.start_background_task(open_betting, table_id, delay)


def resolve_game(table_id):
    """
    Compares each player's score to the dealer's and determines win/loss/push.
    Updates chips accordingly, then broadcasts the results and final game state.
    """
    room = game_rooms.get(table_id)
    if not room:
        print(f"[RESOLVE] Room {table_id} not found.")
        return

    dealer_score = room['dealer']['score']
    results = {}

    for pid, player in room['players'].items():
        bet = player.get("bet", 0)
        p_score = player.get("score", 0)
        outcome = "lose"  # default

        if bet <= 0:
            results[pid] = {"result": "no_bet", "chips": player["chips"]}
            continue

        # Bust → automatic loss
        if p_score > 21:
            outcome = "bust"

        # Dealer busts → player wins if not busted
        elif dealer_score > 21 and p_score <= 21:
            outcome = "win"
            player["chips"] += bet * 2

        # Player beats dealer
        elif p_score > dealer_score and p_score <= 21:
            outcome = "win"
            player["chips"] += bet * 2

        # Push (tie) → return bet
        elif p_score == dealer_score:
            outcome = "push"
            player["chips"] += bet

        # Blackjack bonus (3:2 payout if initial hand = 21)
        if outcome == "win" and p_score == 21 and len(player["hand"]) == 2:
            bonus = int(bet * 0.5)
            player["chips"] += bonus
            print(f"[RESOLVE] Blackjack bonus for {pid}: +{bonus} chips")

        results[pid] = {"result": outcome, "chips": player["chips"]}
        player["bet"] = 0  # Reset bet

    # Mark game state
    room["results"] = results
    room["game_over"] = True
    room["started"] = False
    room["current_turn"] = None

    # Reveal full dealer hand in the final state
    socketio.emit("game_over", {
        "dealer": room["dealer"],
        "players": results
    }, room=table_id)

    emit_game_state(room, table_id)


    print(f"[RESOLVE] Results for table {table_id}: {results}")


def place_bet(table_id, player_id, amount):
    room = rooms.get(table_id)
    if not room:
        return

    player = room["players"].get(player_id)
    if not player:
        return

    # --- Validate bet ---
    if amount <= 0 or amount > player["chips"]:
        emit("error", {"msg": "Invalid bet amount"}, to=player_id)
        return

    # Deduct chips immediately
    player["chips"] -= amount
    player["bet"] = amount
    player["status"] = "bet"

    print(f"[BET] Player {player_id} bet {amount} chips at table {table_id}")

    emit_game_state(room, table_id)

    # --- Check if everyone bet ---
    if all(p["bet"] > 0 for p in room["players"].values()):
        print(f"[ROUND] All players bet → auto-dealing at table {table_id}")
        start_game(table_id)



@socketio.on("leave")
def handle_leave(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    sid = request.sid

    if not table_id or not player_id:
        print(f"Leave failed: missing tableId or playerId from SID {sid}.")
        socketio.emit("error", {"message": "Missing information to leave room."}, to=sid)
        return

    print(f"Player {player_id} (SID: {sid}) attempting to leave room {table_id}.")

    if table_id in game_rooms:
        room = game_rooms[table_id]
        if player_id in room["players"] and room["players"][player_id].get("sid") == sid:
            # Remove player from the room's player list
            del room["players"][player_id]
            print(f"Removed player {player_id} from room {table_id}.")
        else:
            print(f"Player {player_id} not found or SID mismatch in room {table_id}.")

        # Leave the Socket.IO room
        leave_room(table_id, sid=sid)

        if not room["players"]:
            # If no players left, delete the room
            print(f"Room {table_id} is now empty. Deleting room.")
            del game_rooms[table_id]
        else:
            # If there are still players, update everyone else's state
            print(f"Room {table_id} still has players. Updating state.")
            # Emit updated player list after removal
            player_list = [{"id": pid, "username": p["username"]} for pid, p in room["players"].items()]
            socketio.emit("players_update", player_list, room=table_id)
            # Emit game state to remaining players (will adjust to next turn if applicable)
            emit_game_state(room, table_id)
    else:
        print(f"Attempted to leave non-existent room {table_id}.")


def emit_game_state(room_id, reveal=False):
    """
    Emits the game state to ALL players in the room,
    sending each player a private view of their own cards and a public view for others.
    No need to pass requesting_sid anymore.
    """
    game = games[room_id]
    state = {
        "players": [],
        "dealer": {
            "hand": [],
            "hand_value": None
        },
        "started": game["stared"],
        "current_turn": game["current_turn"],
        "game_over": game["game_over"]
    }

    # Dealer's hand
    if reveal or game["game_over"]:
        state["dealer"]["hand"] = game["dealer"]["hand"]
        state["dealer"]["hand_value"] = calculate_hand_value(game["dealer"]["hand"])
    else:
        state["dealer"]["hand"] = [game["dealer"]["hand"][0], {"hiddn": True}]
        state["dealer"]["hand_value"] = None

    # Players' hands
        for sid, pdata in game["players"].items():
            player_state = {
                "id": sid,
                "chips": pdata["chips"],
                "bet": pdata["bet"],
                "hand": [],
                "hand_value": None
            }
            if sid == request.sid or reveal or game["game_over"]:
                player_state["hand"] = pdata["hand"]
                player_state["hand_value"] = calculate_hand_value(pdata["hand"])
            else:
                player_state["hand"] = [{"hidden": True}] * len(pdata["hand"])
            state["players"].append(player_state)

        socketio.emit("game_state", state, room=room_id)


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    tables_to_delete = []

    for table_id, room in list(game_rooms.items()):
        to_remove_pids = [pid for pid, player in room.get("players", {}).items() if player.get("sid") == sid]
        if not to_remove_pids:
            continue

        for pid in to_remove_pids:
            leave_room(table_id, sid=sid)
            if pid in room["players"]:
                del room["players"][pid]
            print(f"Removed disconnected player {pid} from table {table_id}.")

        # if no players left, mark table to delete
        if not room["players"]:
            tables_to_delete.append(table_id)
            print(f"Table {table_id} is now Empty.")

        else:
            # send updated roster
            player_list = [
                {
                "id": pid,
                "username": p["username"]
                 }
                 for pid, p in room["players"].items()]
            socketio.emit("players_update", player_list, room=table_id)

            # if current turn was disconnected, advance
            if room.get("current_turn") in to_remove_pids and not room.get("game_over"):
                print(f"Disconnected current-turn player at {table_id}, advancing turn.")
                advance_turn(room, table_id)
            else:
                emit_game_state(room, table_id)


    for table_id in tables_to_delete:
        print(f"Deleting empty table {table_id}.")
        del game_rooms[table_id]


def public_dealer_hand(dealer, game_over):
    """
    Prepares the dealer's hand for public view.
    If game is over, reveals all cards. Otherwise, hides the second card.
    """
    # print(f"public_dealer_hand called with dealer: {dealer}, game_over: {game_over}") # Uncomment for debugging

    # Define the hidden card placeholder object
    hidden_card_placeholder = {
        "image": "cardBack",  # Ensure this path matches your frontend asset
        "code": "HIDDEN_CARD",      # Unique code for hidden card
        "rank": "HIDDEN",
        "suit": "HIDDEN"
    }

    if not dealer or "hand" not in dealer or len(dealer["hand"]) == 0:
        # Dealer hand not ready yet, return empty or placeholder
        return {"hand": [], "score": 0}

    if game_over:
        # Show full dealer hand if game over
        return {"hand": dealer["hand"], "score": dealer["score"]}
    else:
        # Show only first card, hide second
        first_card = dealer["hand"][0]
        # Calculate partial score for the revealed card
        partial_score = 0
        if first_card and first_card.get('rank'):
            rank = first_card.get('rank')
            values = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5,
                      '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
                      'J': 10, 'Q': 10, 'K': 10}
            if rank in values:
                partial_score = values[rank]
            elif rank.isdigit():
                partial_score = int(rank)

        return {"hand": [first_card, hidden_card_placeholder], "score": partial_score}


@socketio.on('reset_game')
def handle_reset_game(data):
    table_id = data.get('tableId')
    room = game_rooms.get(table_id)
    if not room:
        socketio.emit("error", {"message": "Room not found for reset."}, to=request.sid)
        return

    # reset players (keep their chips)
    for player in room.get("players", {}).values():
        player['hand'] = []
        player['score'] = 0
        player['status'] = "waiting"
        player['bet'] = 0
        player['result'] = "none"

    # reset dealer
    room["dealer"] = {"hand": [], "score": 0}
    room["started"] = False
    room["game_over"] = False
    room["current_turn"] = None
    room["reveal_dealer_hand"] = False

    # fresh deck
    try:
        room["deck"] = create_deck()
        random.shuffle(room["deck"])
    except Exception as e:
        print(f"[RESET] Deck creation failed: {e}")
        socketio.emit("error", {"message": "Failed to create a new deck on reset."}, room=table_id)
        return

    emit_game_state(room, table_id)


@socketio.on("chat_message")
def handle_chat_message(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    message = (data.get("message") or "").strip()
    username = data.get("username", "Anonymous") # Fallback username


    print(f"Chat received: {data}")

    if not message:
        print(f"Empty chat message received from {player_id}.")
        return

    is_global = data.get('isglobal', False)
    target_room = None


    # Determine room + username

    room = game_rooms.get(table_id)
    if room and player_id in room.get("players", {}):
        username = room["players"][player_id]["username"]
        is_global = False
        target_room = table_id
    else:
        is_global = True


    chat_data = {
        "playerId": player_id,
        "username": username,
        "message": message,
        "isGlobal": is_global,
        "tableId": table_id if not is_global else None,
        "timestamp": datetime.now(timezone.utc).isoformat()


    }

    if target_room:
        socketio.emit("chat_message", chat_data, room=target_room)
    else:
        socketio.emit("chat_message", chat_data, broadcast=True)


if __name__ == "__main__":
    print("Starting Flask-SocketIO application...")
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True) # allow_unsafe_werkzeug=True for development
    print("Flask-SocketIO application stopped.")