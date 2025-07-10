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
        # Log the error response for more debugging info
        print(f"Failed to fetch deck from external API. Status: {response.status_code}, Response: {response.text}")
        raise Exception("Failed to fetch deck from external API.")

    cards = response.json()["cards"]

    # Debugging: Print fetched cards to see their raw structure from API
    # for card in cards:
    #     print("Fetched card:", card)

    return [
        {
            "suit": suits_map.get(card["suit"], card["suit"]),
            "rank": rank_map.get(card["value"], card["value"]) if card["value"] != "0" else "10",
            "image": card["image"],
            "code": card["code"] # Include card code for unique keys in frontend if needed
        }
        for card in cards
    ]


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

    if room["started"]:
        print(f"Game in room {table_id} already started.")
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

    room["started"] = True
    room["game_over"] = False

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
        room["dealer"] = {
            "hand": dealer_hand,
            "score": calculate_score(dealer_hand) # Calculate full score for backend, public_dealer_hand hides one.
        }
        print(f"Dealer dealt: {dealer_hand}, score: {room['dealer']['score']}")
    except IndexError:
        print(f"[ERROR] Deck ran out of cards while dealing to dealer in room {table_id}.")
        return jsonify({"error": "Deck ran out of cards during initial deal (dealer)."}), 500
    except Exception as e:
        print(f"[ERROR] Failed to calculate dealer score after initial deal: {e}")
        return jsonify({"error": "Failed to calculate dealer score."}), 500

    # Set the first player's turn (simple example, you might need a more robust turn management)
    if room["players"]:
        room["current_turn"] = next(iter(room["players"])) # First player in the dict

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

    if not table_id or not player_id or bet is None:
        emit('error', {'message': 'Invalid bet request: Missing data'}, to=sid)
        print(f"Invalid bet request from SID {sid}: Missing tableId, playerId, or bet.")
        return

    room = game_rooms.get(table_id)
    if not room:
        emit('error', {'message': 'Room not found'}, to=sid)
        print(f"Room {table_id} not found for bet request from {player_id}.")
        return

    player = room['players'].get(player_id)
    if not player:
        emit('error', {'message': 'Player not found in room'}, to=sid)
        print(f"Player {player_id} not found in room {table_id} for bet request.")
        return

    # Initialize chips if not set
    if 'chips' not in player:
        player['chips'] = 1000
        print(f"Player {player_id} chips initialized to 1000.")

    # Validate bet amount
    if bet < 0: # Allow 0 bet for waiting players as intended
        emit('error', {'message': 'Bet cannot be negative.'}, to=sid)
        print(f"Player {player_id} attempted negative bet: {bet}.")
        return
    if bet > player['chips']:
        emit('error', {'message': f'Not enough chips. You have {player["chips"]}.'}, to=sid)
        print(f"Player {player_id} attempted bet {bet} but only has {player['chips']} chips.")
        return

    if room["started"]:
        emit('error', {'message': 'Cannot place bet, game has already started.'}, to=sid)
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
    emit('bet_placed', {
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
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    username = data.get("username")

    if not all([table_id, player_id, username]):
        print("Join failed: missing data", data)
        emit("error", {"message": "Missing information to join room."}, to=request.sid)
        return

    print(f" Before Join (room {table_id}): {list(game_rooms.get(table_id, {}).get('players', {}).keys())}")

    if table_id not in game_rooms:
        emit("room_not_found", {}, to=request.sid)
        print(f"Room {table_id} not found for join request from {username} ({player_id}).")
        return

    room = game_rooms[table_id]

    # Leave other rooms the SID might be in, to ensure client is only in one game room
    current_rooms = rooms(request.sid)
    for r in current_rooms:
        if r != request.sid and r != table_id:
            leave_room(r)
            print(f"SID {request.sid} left room {r} before joining {table_id}.")

    join_room(table_id) # Join the requested room

    if player_id not in room["players"]:
        room["players"][player_id] = {
            "username": username,
            "hand": [],
            "score": 0,
            "status": "waiting", # Player starts as waiting
            "chips": 1000, # Initial chips
            "bet": 0, # Initial bet
            "sid": request.sid
        }
        print(f"New player {username} ({player_id}) joined room {table_id}.")
    else:
        # Update SID if player is rejoining or reconnecting
        room["players"][player_id]["sid"] = request.sid
        print(f"Existing player {username} ({player_id}) reconnected to room {table_id}.")


    print(f"[JOIN] player_id={player_id}, sid={request.sid}, table={table_id}, username={username}")
    print(f"After Join (room {table_id}): {list(room['players'].keys())}")

    emit("joined_room", {"tableId": table_id}, to=request.sid)

    # Emit updated player list to all in the room
    player_list = [{"id": pid, "username": p["username"]} for pid, p in room["players"].values()]
    emit("players_update", player_list, room=table_id)

    # Emit initial game state to the joining player (private view)
    # The `emit_game_state` function now handles public/private views correctly
    emit_game_state(room, table_id, request.sid)


@socketio.on("hit")
def handle_hit(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    if not table_id or not player_id:
        emit("error", {"message": "Invalid hit request: Missing data."}, to=request.sid)
        print(f"Invalid hit request from SID {request.sid}: Missing tableId or playerId.")
        return

    room = game_rooms.get(table_id)
    if not room or player_id not in room["players"]:
        emit("error", {"message": "Invalid table or player for hit action."}, to=request.sid)
        print(f"Invalid table ({table_id}) or player ({player_id}) for hit action from SID {request.sid}.")
        return

    player = room["players"][player_id]

    # Basic turn management (can be expanded for multiple players taking turns)
    if room.get("current_turn") != player_id:
        emit("error", {"message": "It's not your turn."}, to=request.sid)
        print(f"Player {player_id} tried to hit out of turn in room {table_id}.")
        return

    if player["status"] in ["bust", "stay"]:
        emit("error", {"message": "You cannot hit after staying or busting."}, to=request.sid)
        print(f"Player {player_id} tried to hit after being {player['status']} in room {table_id}.")
        return

    if len(room["deck"]) == 0:
        print(f"Deck empty for room {table_id}, creating new deck.")
        try:
            new_deck = create_deck()
            room["deck"].extend(new_deck) # Use extend to add all elements
            random.shuffle(room["deck"])
        except Exception as e:
            print(f"[ERROR] Failed to replenish deck during hit action for room {table_id}: {e}")
            emit("error", {"message": "Failed to replenish deck. Please try again."}, to=request.sid)
            return

    try:
        card = room["deck"].pop()
        player["hand"].append(card)
        player["score"] = calculate_score(player["hand"])
        print(f"Player {player_id} hit: {card['rank']} {card['suit']}. New score: {player['score']}")
    except IndexError:
        print(f"[ERROR] Deck ran out of cards during hit for player {player_id} in room {table_id}.")
        emit("error", {"message": "Deck ran out of cards."}, to=request.sid)
        return
    except Exception as e:
        print(f"[ERROR] Error processing hit for player {player_id} in room {table_id}: {e}")
        emit("error", {"message": "An error occurred while hitting."}, to=request.sid)
        return

    if player["score"] > 21:
        player["status"] = "bust"
        print(f"Player {player_id} busted with score {player['score']}.")
        # Advance turn after bust
        advance_turn(room, table_id)
    else:
        emit_game_state(room, table_id) # Update state after successful hit

@socketio.on("stay")
def handle_stay(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")

    if not table_id or not player_id:
        emit("error", {"message": "Invalid stay request: Missing data."}, to=request.sid)
        print(f"Invalid stay request from SID {request.sid}: Missing tableId or playerId.")
        return

    room = game_rooms.get(table_id)
    if not room or player_id not in room["players"]:
        emit("error", {"message": "Invalid table or player for stay action."}, to=request.sid)
        print(f"Invalid table ({table_id}) or player ({player_id}) for stay action from SID {request.sid}.")
        return

    player = room["players"][player_id]

    # Basic turn management
    if room.get("current_turn") != player_id:
        emit("error", {"message": "It's not your turn."}, to=request.sid)
        print(f"Player {player_id} tried to stay out of turn in room {table_id}.")
        return

    if player["status"] in ["bust", "stay"]:
        emit("error", {"message": "You already stayed or busted."}, to=request.sid)
        print(f"Player {player_id} tried to stay after being {player['status']} in room {table_id}.")
        return

    player["status"] = "stay"
    print(f"Player {player_id} chose to stay with score {player['score']}.")

    # Advance turn after stay
    advance_turn(room, table_id)


def advance_turn(room, table_id):
    """ Advances the turn to the next player, or makes dealer play if all players are done. """
    player_ids = list(room["players"].keys())
    current_player_idx = player_ids.index(room["current_turn"]) if room["current_turn"] in player_ids else -1

    next_player_id = None
    # Find next player who is still "playing"
    for i in range(1, len(player_ids) + 1):
        next_idx = (current_player_idx + i) % len(player_ids)
        candidate_player_id = player_ids[next_idx]
        if room["players"][candidate_player_id]["status"] == "playing":
            next_player_id = candidate_player_id
            break

    if next_player_id:
        room["current_turn"] = next_player_id
        print(f"Turn advanced to player {next_player_id} in room {table_id}.")
        emit_game_state(room, table_id)
    else:
        # All players are done (bust or stay), dealer plays
        print(f"All players done in room {table_id}. Dealer's turn.")
        room["current_turn"] = "dealer" # Indicate dealer's turn
        dealer_plays(room, table_id)


def dealer_plays(room, table_id):
    """ Dealer logic for drawing cards until 17 or more. """
    dealer = room["dealer"]
    print(f"Dealer's turn in room {table_id}. Initial dealer score: {dealer['score']}")

    while dealer["score"] < 17:
        if len(room["deck"]) == 0:
            print(f"Deck empty for room {table_id}, creating new deck for dealer.")
            try:
                new_deck = create_deck()
                room["deck"].extend(new_deck)
                random.shuffle(room["deck"])
            except Exception as e:
                print(f"[ERROR] Failed to replenish deck during dealer play for room {table_id}: {e}")
                # This is a critical error during gameplay, might need to end game or reset.
                emit("error", {"message": "Dealer could not draw due to deck issue."}, room=table_id)
                room["game_over"] = True # Force game over
                emit_game_state(room, table_id)
                return

        try:
            card = room["deck"].pop()
            dealer["hand"].append(card)
            dealer["score"] = calculate_score(dealer["hand"])
            print(f"Dealer hit: {card['rank']} {card['suit']}. New score: {dealer['score']}")
        except IndexError:
            print(f"[ERROR] Deck ran out of cards during dealer play in room {table_id}.")
            emit("error", {"message": "Deck ran out of cards during dealer's turn."}, room=table_id)
            room["game_over"] = True # Force game over
            emit_game_state(room, table_id)
            return
        except Exception as e:
            print(f"[ERROR] Error processing dealer hit in room {table_id}: {e}")
            emit("error", {"message": "An error occurred during dealer's turn."}, room=table_id)
            room["game_over"] = True # Force game over
            emit_game_state(room, table_id)
            return

    print(f"Dealer finished with score: {dealer['score']} in room {table_id}.")
    resolve_game(table_id)


def resolve_game(table_id):
    room = game_rooms[table_id]
    dealer_score = room['dealer']['score'] # Use pre-calculated score

    print(f"Resolving game for table {table_id}. Dealer final score: {dealer_score}")

    for player_id, player in room['players'].items():
        bet = player.get('bet', 0)
        player_score = player.get('score', 0)

        # Ensure chips key exists
        player.setdefault("chips", 0)
        player.setdefault("result", "none") # Default result

        if player['status'] == 'bust' or player_score > 21:
            player['result'] = 'lose'
            # Chips already deducted for bet, no return
            print(f"Player {player_id} busted. Result: {player['result']} | Chips: {player['chips']}")
        elif dealer_score > 21:
            player['result'] = 'win'
            player['chips'] += bet * 2 # Bet returned + 1x winnings
            print(f"Player {player_id} won (dealer busted). Result: {player['result']} | Chips: {player['chips']}")
        elif player_score > dealer_score:
            player['result'] = 'win'
            player['chips'] += bet * 2 # Bet returned + 1x winnings
            print(f"Player {player_id} won. Result: {player['result']} | Chips: {player['chips']}")
        elif player_score == dealer_score:
            player['result'] = 'push'
            player['chips'] += bet # Bet returned
            print(f"Player {player_id} pushed. Result: {player['result']} | Chips: {player['chips']}")
        else: # player_score < dealer_score
            player['result'] = 'lose'
            # Chips already deducted for bet, no return
            print(f"Player {player_id} lost. Result: {player['result']} | Chips: {player['chips']}")

        # Reset bet for next round
        player['bet'] = 0


    room['game_over'] = True
    room["started"] = False # Game is no longer in "started" state
    room["current_turn"] = None # Reset turn

    # Emit a specific game_over event (optional, but good for frontend specific actions)
    emit('game_over', {
        'players': {
            pid: {
                'result': p['result'],
                'chips': p['chips'],
                'hand': p['hand'], # Send full hand for results display
                'score': p['score']
            } for pid, p in room['players'].items()
        },
        'dealer': room['dealer'] # Dealer's full hand is now revealed
    }, room=table_id)

    # Then emit the general game_state which will now include all revealed hands
    emit_game_state(room, table_id)


@socketio.on("leave")
def handle_leave(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    sid = request.sid

    if not table_id or not player_id:
        print(f"Leave failed: missing tableId or playerId from SID {sid}.")
        emit("error", {"message": "Missing information to leave room."}, to=sid)
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
            player_list = [{"id": pid, "username": p["username"]} for pid, p in room["players"].values()]
            emit("players_update", player_list, room=table_id)
            # Emit game state to remaining players (will adjust to next turn if applicable)
            emit_game_state(room, table_id)
    else:
        print(f"Attempted to leave non-existent room {table_id}.")


def emit_game_state(room, table_id, requesting_sid=None):
    """
    Emits the game state to all clients in a room,
    showing private hand data to the requesting_sid, and public/hidden data to others.
    """
    if not room:
        print(f"[WARNING] emit_game_state called with empty room object for table_id: {table_id}")
        return

    # Prepare hidden card placeholder object
    hidden_card_placeholder = {
        "image": "/card-back.png",  # Ensure this path matches your frontend asset
        "code": "HIDDEN_CARD",      # Unique code for hidden card
        "rank": "HIDDEN",
        "suit": "HIDDEN"
    }

    players_state = {}
    for pid, pdata in room.get("players", {}).items():
        # Determine if this player's hand should be revealed (it's their view or game is over)
        if (requesting_sid and pdata.get("sid") == requesting_sid) or room.get("game_over", False):
            players_state[pid] = {
                "username": pdata["username"],
                "hand": pdata["hand"],
                "score": pdata["score"],
                "status": pdata["status"],
                "chips": pdata["chips"],
                "bet": pdata["bet"],
                "result": pdata.get("result", "none"), # Include result after game is over
                "is_current_turn": room.get("current_turn") == pid
            }
        else:
            # For other players, hide their cards, and don't reveal their score
            hidden_hand = [hidden_card_placeholder for _ in range(len(pdata["hand"]))]
            players_state[pid] = {
                "username": pdata["username"],
                "hand": hidden_hand,
                "score": None, # Score is hidden for others
                "status": pdata["status"],
                "chips": pdata["chips"], # Chips/bet can be public knowledge
                "bet": pdata["bet"],
                "result": pdata.get("result", "none"),
                "is_current_turn": room.get("current_turn") == pid
            }

    # Determine dealer's hand visibility
    dealer_hand_for_frontend = public_dealer_hand(room.get("dealer", {}), room.get("game_over", False))

    state_to_emit = {
        "players": players_state,
        "dealer": dealer_hand_for_frontend,
        "deckCount": len(room.get("deck", [])),
        "game_over": room.get("game_over", False),
        "current_turn": room.get("current_turn") # Send current turn player_id
    }

    # Emit to the requesting_sid (if any) with their specific view
    if requesting_sid:
        emit("game_state", state_to_emit, to=requesting_sid)

        # Emit to all others in the room, excluding the requesting_sid
        # This prevents sending duplicate data to the requesting_sid
        emit("game_state", state_to_emit, room=table_id, skip_sid=requesting_sid)
    else:
        # If no specific requesting_sid, emit the default (all-public/hidden) view to the whole room
        emit("game_state", state_to_emit, room=table_id)


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"Client {sid} disconnected.")

    tables_to_delete = []
    for table_id, room in list(game_rooms.items()):
        player_removed = False
        to_remove_pids = []
        for pid, player in room["players"].items():
            if player.get("sid") == sid:
                to_remove_pids.append(pid)

        for pid in to_remove_pids:
            leave_room(table_id, sid=sid) # Ensure the sid leaves the Socket.IO room
            del room["players"][pid]
            player_removed = True
            print(f"Removed disconnected player {pid} from table {table_id}.")

        if player_removed:
            # If a player was removed, update players_update and game state for remaining
            if not room["players"]:
                tables_to_delete.append(table_id)
                print(f"Table {table_id} is now empty.")
            else:
                player_list = [{"id": pid, "username": p["username"]} for pid, p in room["players"].values()]
                emit("players_update", player_list, room=table_id)
                # If the disconnected player was the current turn, advance turn
                if room.get("current_turn") == to_remove_pids[0] and not room["game_over"]:
                    print(f"Disconnected player {to_remove_pids[0]} was current turn, advancing turn in {table_id}.")
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
        "image": "/card-back.png",  # Ensure this path matches your frontend asset
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


@socketio.on("chat_message")
def handle_chat_message(data):
    table_id = data.get("tableId")
    player_id = data.get("playerId")
    message = data.get("message")
    username = data.get("username", "Anonymous") # Fallback username

    if not message:
        print(f"Empty chat message received from {player_id}.")
        return

    is_global = True
    target_room = None

    if table_id and table_id in game_rooms:
        room = game_rooms[table_id]
        if player_id and player_id in room["players"]:
            username = room["players"][player_id]["username"]
            is_global = False
            target_room = table_id
        else:
            # If table_id is provided but player_id is not in that room
            print(f"Chat message with table_id {table_id} from unknown player {player_id}. Treating as global.")
    else:
        print(f"Chat message without valid table_id. Treating as global.")

    chat_data = {
        "playerId": player_id,
        "username": username,
        "message": message,
        "isGlobal": is_global, # Changed to camelCase for frontend consistency
        "tableId": table_id if not is_global else None, # Only send tableId if not global
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if target_room:
        emit("chat_message", chat_data, room=target_room)
    else:
        emit("chat_message", chat_data, broadcast=True)

if __name__ == "__main__":
    print("Starting Flask-SocketIO application...")
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True) # allow_unsafe_werkzeug=True for development
    print("Flask-SocketIO application stopped.")