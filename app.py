import eventlet
eventlet.monkey_patch()

import uuid

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from game_logic import SnakeGame


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
    # Generate a unique player ID
    player_id = str(uuid.uuid4())  # Unique ID for the player
    
    # Store the player ID and initialize their snake
    game.add_snake(player_id)
    
    # Send the player ID to the client, along with the initial game state
    emit('game_state', {'player_id': player_id, 'snakes': game.snakes, 'food': game.food}, broadcast=True)

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
    # Generate leaderboard based on the snake lengths (or any other scoring method)
    leaderboard = sorted([(player_id, len(snake['body'])) for player_id, snake in game.snakes.items()], key=lambda x: x[1], reverse=True)
    
    # Emit the game state with the leaderboard included
    emit('game_state', {'snakes': game.snakes, 'food': game.food, 'leaderboard': leaderboard}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, log_output=True)





