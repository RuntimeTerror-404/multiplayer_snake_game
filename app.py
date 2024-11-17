import eventlet
eventlet.monkey_patch()
import random

import uuid

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from game_logic import SnakeGame

# Define a dictionary to store player data
players = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

game = SnakeGame()

@app.route('/')
def index():
    return "Server is up!"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Server is running'})

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('message', {'data': 'Connected successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('join_game')
def on_join(data):
    player_id = data.get('player_id', str(uuid.uuid4()))  # Generate a new player_id if not provided
    game.snakes[player_id] = {
        'body': [[random.randint(0, 20), random.randint(0, 20)] for _ in range(3)],
        'direction': 'RIGHT',
        'score': 0
    }
    print(f"Player {player_id} joined the game.")
    socketio.emit('game_state', {
        'player_id': player_id,
        'snakes': game.snakes,
        'food': game.food
    })

@socketio.on('move')
def on_move(data):
    player_id = data['player_id']
    direction = data['direction']
    game.set_direction(player_id, direction)
    
    if not game.move_snake(player_id):
        emit('game_over', {'player_id': player_id})
    else:
        # Emit the updated game state, including the leaderboard
        leaderboard = game.get_leaderboard()
        emit('game_state', {'snakes': game.snakes, 'food': game.food, 'leaderboard': leaderboard}, broadcast=True)

@socketio.on('message')
def handle_message(data):
    print(f"Received message: {data}")
    emit('message', {'data': f"Server response: {data}"})

@socketio.on('game_state')
def on_game_state():
    # Update the score for each snake based on its length
    for player_id, snake in game.snakes.items():
        snake['score'] = len(snake['body'])  # Using body length as score

    # Generate leaderboard sorted by score (length of snake)
    leaderboard = sorted(
        [(player_id, snake['score']) for player_id, snake in game.snakes.items()],
        key=lambda x: x[1], reverse=True
    )
    
    # Emit the game state with leaderboard included
    emit('game_state', {'snakes': game.snakes, 'food': game.food, 'leaderboard': leaderboard}, broadcast=True)


@socketio.on('move_snake')
def move_snake(data):
    player_id = data['player_id']
    direction = data['direction']
    if player_id in game.snakes:
        snake = game.snakes[player_id]

        # Update direction and check movement logic
        if direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            snake['direction'] = direction
            head = list(snake['body'][0])
            if direction == 'UP':
                head[1] -= 1
            elif direction == 'DOWN':
                head[1] += 1
            elif direction == 'LEFT':
                head[0] -= 1
            elif direction == 'RIGHT':
                head[0] += 1

            snake['body'].insert(0, head)
            snake['body'].pop()  # Keep body length same initially

            # Check food collision
            if head == game.food:
                snake['score'] += 1
                game.food = [random.randint(0, 20), random.randint(0, 20)]

        # Emit updated state to all clients
        socketio.emit('game_state', {
            'player_id': player_id,
            'snakes': game.snakes,
            'food': game.food
        })


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, log_output=True)





