import pygame
import random
from enum import Enum
import time


class Direction(Enum):
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class TetrisGame:
    BLOCK_SIZE = 30
    BOARD_WIDTH = 10
    BOARD_HEIGHT = 20
    PREVIEW_SIZE = 4
    SHAPES = [
        [[1, 1, 1, 1]],  # I
        [[1, 1], [1, 1]],  # O
        [[1, 1, 1], [0, 1, 0]],  # T
        [[1, 1, 1], [1, 0, 0]],  # L
        [[1, 1, 1], [0, 0, 1]],  # J
        [[1, 1, 0], [0, 1, 1]],  # S
        [[0, 1, 1], [1, 1, 0]]  # Z
    ]
    COLORS = [
        (0, 255, 255),  # cyan
        (255, 255, 0),  # yellow
        (255, 0, 255),  # purple
        (255, 165, 0),  # orange
        (0, 0, 255),  # blue
        (0, 255, 0),  # green
        (255, 0, 0)  # red
    ]
    # Official Tetris scoring system
    SCORING = {
        1: 100,  # Single line
        2: 300,  # Double
        3: 500,  # Triple
        4: 800  # Tetris
    }
    LINES_PER_LEVEL = 10  # Number of lines needed to advance to next level

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tetris")

        # Calculate window dimensions
        self.sidebar_width = 200
        self.window_width = self.BLOCK_SIZE * self.BOARD_WIDTH + self.sidebar_width
        self.window_height = self.BLOCK_SIZE * self.BOARD_HEIGHT

        # Create display surfaces
        self.window = pygame.display.set_mode((self.window_width, self.window_height))
        self.game_surface = pygame.Surface((self.BLOCK_SIZE * self.BOARD_WIDTH, self.window_height))
        self.preview_surface = pygame.Surface(
            (self.BLOCK_SIZE * self.PREVIEW_SIZE, self.BLOCK_SIZE * self.PREVIEW_SIZE))

        # Initialize font
        self.font = pygame.font.Font(None, 36)

        # Game state
        self.board = [[0 for _ in range(self.BOARD_WIDTH)] for _ in range(self.BOARD_HEIGHT)]
        self.current_piece = None
        self.current_pos = None
        self.current_shape_index = None
        self.next_shape_index = None
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False

        # Timer for handling key repeats
        self.down_pressed = False
        self.last_move_time = 0
        self.move_delay = 100  # milliseconds
        self.clock = pygame.time.Clock()

        # Start game
        self.next_shape_index = random.randint(0, len(self.SHAPES) - 1)
        self.spawn_piece()

    def spawn_piece(self):
        if self.next_shape_index is None:
            self.next_shape_index = random.randint(0, len(self.SHAPES) - 1)

        self.current_shape_index = self.next_shape_index
        self.current_piece = [row[:] for row in self.SHAPES[self.current_shape_index]]
        piece_width = len(self.current_piece[0])
        self.current_pos = [0, self.BOARD_WIDTH // 2 - piece_width // 2]

        # Generate next piece
        self.next_shape_index = random.randint(0, len(self.SHAPES) - 1)

        if self.check_collision():
            self.game_over = True

    def get_ghost_position(self):
        if not self.current_piece:
            return None

        ghost_pos = self.current_pos[:]
        while not self.check_collision(test_pos=ghost_pos):
            ghost_pos[0] += 1
        ghost_pos[0] -= 1

        return ghost_pos

    def draw(self):
        # Clear surfaces
        self.window.fill((0, 0, 0))  # Main window background
        self.game_surface.fill((20, 20, 35))  # Slightly lighter background for game field
        self.preview_surface.fill((0, 0, 0))

        # Draw border around game field
        pygame.draw.rect(
            self.game_surface,
            (40, 40, 60),  # Border color
            (0, 0, self.BLOCK_SIZE * self.BOARD_WIDTH, self.window_height),
            2  # Border thickness
        )

        # Draw ghost piece
        ghost_pos = self.get_ghost_position()
        if ghost_pos:
            for i in range(len(self.current_piece)):
                for j in range(len(self.current_piece[0])):
                    if self.current_piece[i][j]:
                        self.draw_block(
                            ghost_pos[0] + i,
                            ghost_pos[1] + j,
                            self.COLORS[self.current_shape_index],
                            ghost=True
                        )

        # Draw fallen pieces
        for i in range(self.BOARD_HEIGHT):
            for j in range(self.BOARD_WIDTH):
                if self.board[i][j]:
                    self.draw_block(i, j, self.COLORS[self.board[i][j] - 1])

        # Draw current piece
        if self.current_piece:
            for i in range(len(self.current_piece)):
                for j in range(len(self.current_piece[0])):
                    if self.current_piece[i][j]:
                        self.draw_block(
                            self.current_pos[0] + i,
                            self.current_pos[1] + j,
                            self.COLORS[self.current_shape_index]
                        )

        # Draw preview piece
        next_piece = self.SHAPES[self.next_shape_index]
        piece_height = len(next_piece)
        piece_width = len(next_piece[0])
        offset_x = (self.PREVIEW_SIZE - piece_width) * self.BLOCK_SIZE // 2
        offset_y = (self.PREVIEW_SIZE - piece_height) * self.BLOCK_SIZE // 2

        for i in range(piece_height):
            for j in range(piece_width):
                if next_piece[i][j]:
                    pygame.draw.rect(
                        self.preview_surface,
                        self.COLORS[self.next_shape_index],
                        (
                            offset_x + j * self.BLOCK_SIZE,
                            offset_y + i * self.BLOCK_SIZE,
                            self.BLOCK_SIZE - 1,
                            self.BLOCK_SIZE - 1
                        )
                    )

        # Draw score and level
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        level_text = self.font.render(f"Level: {self.level}", True, (255, 255, 255))
        lines_text = self.font.render(f"Lines: {self.lines_cleared}", True, (255, 255, 255))

        # Draw game over
        if self.game_over:
            game_over_text = self.font.render("Game Over!", True, (255, 255, 255))
            text_rect = game_over_text.get_rect(
                center=(self.BLOCK_SIZE * self.BOARD_WIDTH // 2, self.window_height // 2))
            self.game_surface.blit(game_over_text, text_rect)

        # Combine surfaces
        self.window.blit(self.game_surface, (0, 0))
        self.window.blit(score_text, (self.BLOCK_SIZE * self.BOARD_WIDTH + 20, 20))
        self.window.blit(level_text, (self.BLOCK_SIZE * self.BOARD_WIDTH + 20, 60))
        self.window.blit(lines_text, (self.BLOCK_SIZE * self.BOARD_WIDTH + 20, 100))
        self.window.blit(self.preview_surface, (self.BLOCK_SIZE * self.BOARD_WIDTH + 20, 140))

        pygame.display.flip()

    def draw_block(self, row, col, color, ghost=False):
        if ghost:
            # Draw only the outline for ghost piece
            pygame.draw.rect(
                self.game_surface,
                color,
                (
                    col * self.BLOCK_SIZE,
                    row * self.BLOCK_SIZE,
                    self.BLOCK_SIZE - 1,
                    self.BLOCK_SIZE - 1
                ),
                1
            )
        else:
            pygame.draw.rect(
                self.game_surface,
                color,
                (
                    col * self.BLOCK_SIZE,
                    row * self.BLOCK_SIZE,
                    self.BLOCK_SIZE - 1,
                    self.BLOCK_SIZE - 1
                )
            )

    def check_collision(self, test_pos=None):
        if test_pos is None:
            test_pos = self.current_pos

        for i in range(len(self.current_piece)):
            for j in range(len(self.current_piece[0])):
                if self.current_piece[i][j]:
                    new_row = test_pos[0] + i
                    new_col = test_pos[1] + j
                    if (new_row >= self.BOARD_HEIGHT or
                            new_col < 0 or
                            new_col >= self.BOARD_WIDTH or
                            (new_row >= 0 and self.board[new_row][new_col])):
                        return True
        return False

    def merge_piece(self):
        for i in range(len(self.current_piece)):
            for j in range(len(self.current_piece[0])):
                if self.current_piece[i][j]:
                    self.board[self.current_pos[0] + i][self.current_pos[1] + j] = self.current_shape_index + 1

    def clear_lines(self):
        lines_cleared = 0
        i = self.BOARD_HEIGHT - 1
        rows_to_clear = []

        # Find complete lines
        while i >= 0:
            if all(self.board[i]):
                lines_cleared += 1
                rows_to_clear.append(i)
            i -= 1

        # Clear the lines and update score
        if lines_cleared > 0:
            # Update score based on number of lines cleared and current level
            self.score += self.SCORING[lines_cleared] * self.level
            self.lines_cleared += lines_cleared

            # Update level
            new_level = (self.lines_cleared // self.LINES_PER_LEVEL) + 1
            if new_level != self.level:
                self.level = new_level

            # Remove the cleared lines
            for row in sorted(rows_to_clear, reverse=True):
                self.board.pop(row)
                self.board.insert(0, [0] * self.BOARD_WIDTH)

    def move(self, direction):
        if self.game_over:
            return

        old_pos = self.current_pos[:]

        if direction == Direction.DOWN:
            self.current_pos[0] += 1
        elif direction == Direction.LEFT:
            self.current_pos[1] -= 1
        elif direction == Direction.RIGHT:
            self.current_pos[1] += 1

        if self.check_collision():
            self.current_pos = old_pos
            if direction == Direction.DOWN:
                self.merge_piece()
                self.clear_lines()
                self.spawn_piece()

    def rotate(self):
        if self.game_over:
            return

        old_piece = [row[:] for row in self.current_piece]
        rows = len(self.current_piece)
        cols = len(self.current_piece[0])
        self.current_piece = [[self.current_piece[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]

        if self.check_collision():
            self.current_piece = old_piece

    def drop(self):
        if self.game_over:
            return

        while not self.check_collision():
            self.current_pos[0] += 1

        self.current_pos[0] -= 1
        self.merge_piece()
        self.clear_lines()
        self.spawn_piece()

    def handle_input(self):
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # Handle continuous movement with delay
        if current_time - self.last_move_time > self.move_delay:
            if keys[pygame.K_LEFT]:
                self.move(Direction.LEFT)
                self.last_move_time = current_time
            if keys[pygame.K_RIGHT]:
                self.move(Direction.RIGHT)
                self.last_move_time = current_time
            if keys[pygame.K_DOWN]:
                self.move(Direction.DOWN)
                self.last_move_time = current_time

    def run(self):
        last_drop_time = pygame.time.get_ticks()

        running = True
        while running:
            current_time = pygame.time.get_ticks()

            # Calculate drop delay based on level (speeds up as level increases)
            drop_delay = max(1000 - (self.level - 1) * 50, 100)  # Minimum 100ms delay

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.rotate()
                    elif event.key == pygame.K_SPACE:
                        self.drop()

            # Handle continuous input
            self.handle_input()

            # Automatic drop
            if current_time - last_drop_time > drop_delay:
                self.move(Direction.DOWN)
                last_drop_time = current_time

            # Draw game state
            self.draw()

            # Control game speed
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()