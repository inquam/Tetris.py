import tkinter as tk
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
    COLORS = ['cyan', 'yellow', 'purple', 'orange', 'blue', 'green', 'red']

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Tetris")
        self.window.resizable(False, False)

        # Configure key repeat delay
        self.window.bind_all('<Key>', self.handle_keypress)
        self.pressed_keys = set()

        # Create main game frame
        self.game_frame = tk.Frame(self.window)
        self.game_frame.pack(side=tk.LEFT)

        # Create game canvas
        self.canvas = tk.Canvas(
            self.game_frame,
            width=self.BLOCK_SIZE * self.BOARD_WIDTH,
            height=self.BLOCK_SIZE * self.BOARD_HEIGHT,
            bg='black'
        )
        self.canvas.pack()

        # Create side panel
        self.side_panel = tk.Frame(self.window)
        self.side_panel.pack(side=tk.LEFT, padx=20)

        # Score display
        self.score_var = tk.StringVar(value="Score: 0")
        self.score_label = tk.Label(self.side_panel, textvariable=self.score_var)
        self.score_label.pack(pady=10)

        # Next piece preview
        self.preview_canvas = tk.Canvas(
            self.side_panel,
            width=self.BLOCK_SIZE * self.PREVIEW_SIZE,
            height=self.BLOCK_SIZE * self.PREVIEW_SIZE,
            bg='black'
        )
        self.preview_canvas.pack()

        # Game state
        self.board = [[0 for _ in range(self.BOARD_WIDTH)] for _ in range(self.BOARD_HEIGHT)]
        self.current_piece = None
        self.current_pos = None
        self.current_shape_index = None
        self.next_shape_index = None
        self.score = 0
        self.game_over = False
        self.last_down_press = 0

        # Bind keys
        self.window.bind('<Left>', lambda e: self.move(Direction.LEFT))
        self.window.bind('<Right>', lambda e: self.move(Direction.RIGHT))
        self.window.bind('<Down>', self.handle_down_press)
        self.window.bind('<KeyRelease-Down>', self.handle_down_release)
        self.window.bind('<Up>', self.rotate)
        self.window.bind('<space>', self.drop)
        self.window.bind('<Shift-Down>', self.drop)  # Shift + Down for instant drop

        # Game state variables for down key handling
        self.down_pressed = False
        self.fast_drop = False

        # Start game
        self.next_shape_index = random.randint(0, len(self.SHAPES) - 1)
        self.spawn_piece()
        self.update()

    def spawn_piece(self):
        if self.next_shape_index is None:
            self.next_shape_index = random.randint(0, len(self.SHAPES) - 1)

        self.current_shape_index = self.next_shape_index
        self.current_piece = [row[:] for row in self.SHAPES[self.current_shape_index]]
        piece_width = len(self.current_piece[0])
        self.current_pos = [0, self.BOARD_WIDTH // 2 - piece_width // 2]

        # Generate next piece
        self.next_shape_index = random.randint(0, len(self.SHAPES) - 1)
        self.draw_preview()

        if self.check_collision():
            self.game_over = True

    def draw_preview(self):
        self.preview_canvas.delete('all')
        next_piece = self.SHAPES[self.next_shape_index]

        # Calculate centering offsets
        piece_height = len(next_piece)
        piece_width = len(next_piece[0])
        offset_x = (self.PREVIEW_SIZE - piece_width) * self.BLOCK_SIZE // 2
        offset_y = (self.PREVIEW_SIZE - piece_height) * self.BLOCK_SIZE // 2

        for i in range(piece_height):
            for j in range(piece_width):
                if next_piece[i][j]:
                    x1 = offset_x + j * self.BLOCK_SIZE
                    y1 = offset_y + i * self.BLOCK_SIZE
                    x2 = x1 + self.BLOCK_SIZE
                    y2 = y1 + self.BLOCK_SIZE
                    self.preview_canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=self.COLORS[self.next_shape_index],
                        outline='white'
                    )

    def get_ghost_position(self):
        if not self.current_piece:
            return None

        # Find the lowest possible position
        ghost_pos = self.current_pos[:]
        while not self.check_collision(test_pos=ghost_pos):
            ghost_pos[0] += 1
        ghost_pos[0] -= 1

        return ghost_pos

    def draw(self):
        self.canvas.delete('all')

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

    def draw_block(self, row, col, color, ghost=False):
        x1 = col * self.BLOCK_SIZE
        y1 = row * self.BLOCK_SIZE
        x2 = x1 + self.BLOCK_SIZE
        y2 = y1 + self.BLOCK_SIZE

        if ghost:
            # Draw only the outline for ghost piece
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=color,
                width=2,
                fill=''
            )
        else:
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline='white'
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
        while i >= 0:
            if all(self.board[i]):
                lines_cleared += 1
                for k in range(i, 0, -1):
                    self.board[k] = self.board[k - 1][:]
                self.board[0] = [0] * self.BOARD_WIDTH
            else:
                i -= 1

        if lines_cleared:
            self.score += lines_cleared * 100
            self.score_var.set(f"Score: {self.score}")

    def handle_down_press(self, event):
        if self.game_over:
            return
        self.down_pressed = True
        self.fast_drop = True
        self.accelerate_drop()

    def handle_down_release(self, event):
        self.down_pressed = False
        self.fast_drop = False

    def accelerate_drop(self):
        if self.down_pressed and self.fast_drop and not self.game_over:
            self.move(Direction.DOWN)
            self.window.after(50, self.accelerate_drop)  # Faster drop speed while down is pressed

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

        self.draw()

    def rotate(self, event):
        if self.game_over:
            return

        # Save the current piece state
        old_piece = [row[:] for row in self.current_piece]

        # Rotate the piece (90 degrees clockwise)
        rows = len(self.current_piece)
        cols = len(self.current_piece[0])
        self.current_piece = [[self.current_piece[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]

        # If the rotation causes a collision, revert back
        if self.check_collision():
            self.current_piece = old_piece

        self.draw()

    def drop(self, event):
        if self.game_over:
            return

        while not self.check_collision():
            self.current_pos[0] += 1

        self.current_pos[0] -= 1
        self.merge_piece()
        self.clear_lines()
        self.spawn_piece()
        self.draw()

    def handle_keypress(self, event):
        # Track pressed keys to prevent key repeat delay
        self.pressed_keys.add(event.keysym)

    def update(self):
        if not self.game_over:
            self.move(Direction.DOWN)
            self.window.after(1000, self.update)
        else:
            self.canvas.create_text(
                self.BOARD_WIDTH * self.BLOCK_SIZE // 2,
                self.BOARD_HEIGHT * self.BLOCK_SIZE // 2,
                text="Game Over!",
                fill="white",
                font=("Arial", 24)
            )

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()