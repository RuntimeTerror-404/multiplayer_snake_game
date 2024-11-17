import random


class SnakeGame:
    def __init__(self):
        self.board_size = 20
        self.snakes = {}
        self.food = self.generate_food()

    def generate_food(self):
        return [random.randint(0, self.board_size - 1), random.randint(0, self.board_size - 1)]

    def add_snake(self, player_id):
        # Initialize a snake with a length of 3 at a random position
        x, y = random.randint(1, self.board_size - 2), random.randint(1, self.board_size - 2)
        self.snakes[player_id] = {
            'body': [[x, y], [x, y - 1], [x, y - 2]],
            'direction': 'RIGHT',
            'score': 0  # Initialize score based on snake length
        }

    def set_direction(self, player_id, direction):
        if player_id in self.snakes:
            self.snakes[player_id]['direction'] = direction

    def move_snake(self, player_id):
        if player_id not in self.snakes:
            return False

        snake = self.snakes[player_id]
        head = snake['body'][0]
        direction = snake['direction']

        # Determine new head position based on direction
        if direction == 'UP':
            new_head = [head[0], head[1] - 1]
        elif direction == 'DOWN':
            new_head = [head[0], head[1] + 1]
        elif direction == 'LEFT':
            new_head = [head[0] - 1, head[1]]
        elif direction == 'RIGHT':
            new_head = [head[0] + 1, head[1]]
        else:
            return False

        # Check collision with walls
        if not (0 <= new_head[0] < self.board_size and 0 <= new_head[1] < self.board_size):
            return False

        # Check collision with itself
        if new_head in snake['body']:
            return False

        # Move the snake
        snake['body'].insert(0, new_head)

        # Check if food is eaten
        if new_head == self.food:
            self.food = self.generate_food()
            snake['score'] += 1  # Increase score for eating food
        else:
            snake['body'].pop()  # Remove tail if no food eaten

        return True

    def get_leaderboard(self):
        # Return the leaderboard sorted by score
        leaderboard = [(player_id, data['score']) for player_id, data in self.snakes.items()]
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        return leaderboard