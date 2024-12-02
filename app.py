import eventlet

eventlet.monkey_patch()
import random
import uuid
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from game_logic import SnakeGame

# Initialize the Flask app and SocketIO
app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Initialize game logic
game = SnakeGame()

# Player data to track `player_id` by session ID
players = {}  # Store {session_id: player_id}


@app.route("/")
def index():
    return "Server is up!"


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "Server is running"})


@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("message", {"data": "Connected successfully"})


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    player_id = players.pop(sid, None)
    if player_id:
        game.snakes.pop(player_id, None)
        print(f"Player {player_id} disconnected.")
    emit(
        "game_state",
        {"snakes": game.snakes, "food": game.food, "obstacles": game.obstacles},
        broadcast=True,
    )


@socketio.on("join_game")
def on_join(data):
    # Retrieve or generate player_id
    player_name = data.get("player_name", "Unknown Player")
    player_id = data.get("player_id", None)
    if not player_id or player_id not in game.snakes:
        # Generate a new player_id if it's not provided or not found in the game
        player_id = str(uuid.uuid4())
        print(f"Assigning new player ID: {player_id}")

    # Validate player_name
    if not player_name:
        player_name = f"Player_{random.randint(1000, 9999)}"

    # Register player in the game
    if player_id not in game.snakes:
        game.snakes[player_id] = {
            "name": player_name,
            "body": [[random.randint(0, 20), random.randint(0, 20)] for _ in range(3)],
            "direction": "RIGHT",
            "score": 0,
            "lives": 3,
        }
        print(f"{player_name} joined the game with ID: {player_id}")

    players[request.sid] = player_id

    # Prepare leaderboard data (sorted by score)
    leaderboard = sorted(
        [(player_id, snake['score']) for player_id, snake in game.snakes.items()],
        key=lambda x: x[1],
        reverse=True
    )

    # Emit the game state back to the client, including player ID
    socketio.emit(
        "game_state",
        {
            "player_id": player_id,
            "snakes": game.snakes,
            "food": game.food,
            "obstacles": game.obstacles,
            'leaderboard': leaderboard,
        },
    )
    print("obstacles in game: ", game.obstacles)


@socketio.on("move_snake")
def move_snake(data):
    player_id = data.get("player_id", None)

    # Validate player_id
    if player_id is None or player_id not in game.snakes:
        print("Invalid player ID. Player may not have joined properly.")
        emit("error", {"message": "Invalid player ID"})
        return

    # Extract and validate direction
    direction = data.get("direction", None)
    if direction not in ["UP", "DOWN", "LEFT", "RIGHT"]:
        print("Invalid direction received.")
        emit("error", {"message": "Invalid direction"})
        return

    # Move the snake
    snake = game.snakes[player_id]
    snake["direction"] = direction
    head = list(snake["body"][0])
    if direction == "UP":
        head[1] -= 1
    elif direction == "DOWN":
        head[1] += 1
    elif direction == "LEFT":
        head[0] -= 1
    elif direction == "RIGHT":
        head[0] += 1

    # Check collision with obstacles
    for obstacle in game.obstacles:
        if head == obstacle:
            snake["score"] = 0  # Reset score
            snake["lives"] -= 1  # Decrement lives
            if snake["lives"] <= 0:
                del game.snakes[player_id]  # Remove player if out of lives
                emit("game_over", {"player_id": player_id})
                print(f"Player {player_id} removed from the game.")
            break

    snake["body"].insert(0, head)
    snake["body"].pop()

    # Check for food collision
    if head == game.food:
        snake["score"] += 1
        game.food = [random.randint(0, 20), random.randint(0, 20)]
        snake["body"].append(snake["body"][-1])  # Grow snake

    # Prepare leaderboard data (sorted by score)
    leaderboard = sorted(
        [(snake['name'], snake['score'], snake['lives']) for snake in game.snakes.values()],
        key=lambda x: x[1],
        reverse=True
    )


    # Emit the updated game state
    socketio.emit(
        "game_state",
        {
            "player_id": player_id,
            "snakes": game.snakes,
            "food": game.food,
            "obstacles": game.obstacles,
            'leaderboard': leaderboard,
        },
    )


@socketio.on("game_state")
def on_game_state(data=None):
    leaderboard = sorted(
        [
            (player_id, snake["name"], snake["score"])
            for player_id, snake in game.snakes.items()
        ],
        key=lambda x: x[1],
        reverse=True,
    )
    game_state = {
        "snakes": game.snakes,
        "food": game.food,
        "obstacles": game.obstacles,
        "leaderboard": leaderboard,
    }
    print("Obstacles in game state:", game.obstacles)
    socketio.emit("game_state", game_state, broadcast=True)


@socketio.on('chat_message')
def handle_chat_message(data):
    player_name = data.get('player_name', 'Unknown')
    message = data.get('message', '')
    print(f"Chat message from {player_name}: {message}")

    # Broadcast the chat message to all clients
    socketio.emit('chat_message', {'player_name': player_name, 'message': message})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, log_output=True)
