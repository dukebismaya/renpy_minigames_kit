# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
default match_board = None
default match_selected_cell = None
default match_message = "Select two adjacent sigils to swap."
default match_score = 0
default match_turns = 0
default match_target_score = 12
default match_swap_cells = []
default match_match_cells = []
default match_pending_resolution = False
default match_board_locked = False
default match_autoplay = False

init python:
    import random

    class MiniMatchBoard(object):
        def __init__(self, size=3, tile_types=None):
            self.size = size
            self.tile_types = tile_types or ["A", "B", "C", "D", "E"]
            self._build_board()

        def _build_board(self):
            attempts = 0
            while True:
                self.grid = [[self._random_tile() for _ in range(self.size)] for _ in range(self.size)]
                if not self.find_matches() or attempts > 25:
                    break
                attempts += 1

        def _random_tile(self):
            return random.choice(self.tile_types)

        def swap_cells(self, a, b):
            (r1, c1), (r2, c2) = a, b
            self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]

        def are_adjacent(self, a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

        def find_matches(self):
            matches = set()
            size = self.size
            for row in range(size):
                row_vals = self.grid[row]
                if row_vals[0] is not None and len(set(row_vals)) == 1:
                    matches.update((row, col) for col in range(size))

            for col in range(size):
                col_vals = [self.grid[row][col] for row in range(size)]
                if col_vals[0] is not None and len(set(col_vals)) == 1:
                    matches.update((row, col) for row in range(size))

            return matches

        def resolve_all_matches(self):
            cleared = 0
            while True:
                matches = self.find_matches()
                if not matches:
                    break

                for row, col in matches:
                    self.grid[row][col] = None

                cleared += len(matches)
                self._collapse_columns()

            return cleared

        def _collapse_columns(self):
            size = self.size
            for col in range(size):
                column = [self.grid[row][col] for row in range(size) if self.grid[row][col] is not None]
                missing = size - len(column)
                new_tiles = [self._random_tile() for _ in range(missing)]
                combined = new_tiles + column
                for row in range(size):
                    self.grid[row][col] = combined[row]

        def _score_swap(self, a, b):
            self.swap_cells(a, b)
            matches = self.find_matches()
            score = len(matches)
            self.swap_cells(a, b)
            return score, matches

        def best_scoring_swap(self):
            best = None
            best_score = 0
            size = self.size
            for row in range(size):
                for col in range(size):
                    for dr, dc in ((0, 1), (1, 0)):
                        nr = row + dr
                        nc = col + dc
                        if nr >= size or nc >= size:
                            continue
                        score, _matches = self._score_swap((row, col), (nr, nc))
                        if score > best_score:
                            best_score = score
                            best = ((row, col), (nr, nc), score)
            return best

    MATCH_TILE_SIZE = 120
    MATCH_TILE_SPACING = 10
    MATCH_TILE_STEP = MATCH_TILE_SIZE + MATCH_TILE_SPACING

    def reset_match3_state():
        global match_board, match_selected_cell, match_message, match_score, match_turns
        global match_swap_cells, match_match_cells, match_pending_resolution, match_board_locked
        global match_autoplay
        match_board = MiniMatchBoard()
        match_selected_cell = None
        match_message = "Select two adjacent sigils to swap."
        match_score = 0
        match_turns = 10
        match_swap_cells = []
        match_match_cells = []
        match_pending_resolution = False
        match_board_locked = False
        match_autoplay = False

    def handle_match_tile_click(row, col):
        global match_board, match_turns, match_selected_cell, match_message, match_score
        global match_swap_cells, match_match_cells, match_pending_resolution, match_board_locked
        board = match_board
        if not board or match_turns <= 0 or match_board_locked or match_pending_resolution:
            return

        pos = (row, col)

        if match_selected_cell is None:
            match_selected_cell = pos
            match_message = "Choose a neighboring sigil to swap."
            return

        if match_selected_cell == pos:
            match_selected_cell = None
            match_message = "Selection cleared."
            return

        if not board.are_adjacent(match_selected_cell, pos):
            match_selected_cell = None
            match_message = "Sigils must share an edge."
            return

        attempt_match_swap(match_selected_cell, pos, source="manual")

    def match_goal_met():
        return match_score >= match_target_score

    def attempt_match_swap(first_cell, second_cell, source="manual"):
        global match_swap_cells, match_match_cells, match_board_locked
        global match_pending_resolution, match_selected_cell, match_message
        global match_turns, match_board, match_score
        match_selected_cell = None
        if not match_board or match_turns <= 0:
            return False

        match_swap_cells = [
            {"start": first_cell, "end": second_cell},
            {"start": second_cell, "end": first_cell},
        ]
        match_board.swap_cells(first_cell, second_cell)
        match_turns -= 1
        matches = match_board.find_matches()
        if matches:
            match_match_cells = list(matches)
            match_board_locked = True
            match_pending_resolution = True
            if source == "auto":
                match_message = "Autoplay weaving sigils..."
            else:
                match_message = "Sigils resonating..."
            renpy.restart_interaction()
        else:
            match_board.swap_cells(first_cell, second_cell)
            if source == "auto":
                match_message = "Autoplay swap fizzled."
            else:
                match_message = "No match formed."

        if match_turns <= 0 and not match_pending_resolution:
            if match_score >= match_target_score:
                match_message = "Goal reached! Claim your spoils."
            else:
                match_message = "Out of turns. Final score: {}".format(match_score)

        return bool(matches)

    def stop_match_autoplay(message=None):
        global match_autoplay, match_message
        if match_autoplay:
            match_autoplay = False
            if message:
                match_message = message
            renpy.restart_interaction()

    def toggle_match_autoplay():
        global match_autoplay, match_message
        if match_autoplay:
            stop_match_autoplay("Autoplay halted.")
        else:
            match_autoplay = True
            match_message = "Autoplay engaged."
            autoplay_step()
            renpy.restart_interaction()

    def autoplay_step():
        global match_autoplay, match_turns, match_board
        global match_board_locked, match_pending_resolution
        if not match_autoplay:
            return

        if not match_board or match_turns <= 0 or match_goal_met():
            stop_match_autoplay("Autoplay complete.")
            return

        if match_board_locked or match_pending_resolution:
            return

        move = match_board.best_scoring_swap()
        if not move:
            stop_match_autoplay("Autoplay halted; no valid swaps.")
            return

        first_cell, second_cell, _score = move
        attempt_match_swap(first_cell, second_cell, source="auto")

    def finalize_match_resolution():
        global match_pending_resolution, match_board_locked, match_match_cells
        global match_score, match_message, match_turns, match_autoplay
        if not match_pending_resolution or not match_board:
            return

        match_pending_resolution = False
        cleared = match_board.resolve_all_matches()
        if cleared:
            match_score += cleared
            match_message = "Matched {} sigils!".format(cleared)
        else:
            match_message = "Sigils stabilized."

        match_match_cells = []
        match_board_locked = False

        if match_turns <= 0:
            if match_score >= match_target_score:
                match_message = "Goal reached! Claim your spoils."
            else:
                match_message = "Out of turns. Final score: {}".format(match_score)

        if match_autoplay and (match_turns <= 0 or match_goal_met()):
            stop_match_autoplay()

    def clear_match_swap_effect():
        global match_swap_cells
        match_swap_cells = []

    def get_tile_transforms(row, col):
        transforms = []
        for swap in match_swap_cells:
            if swap.get("end") == (row, col):
                dx = (swap["start"][1] - swap["end"][1]) * MATCH_TILE_STEP
                dy = (swap["start"][0] - swap["end"][0]) * MATCH_TILE_STEP
                transforms.append(match_swap_anim(dx=dx, dy=dy))

        if (row, col) in match_match_cells:
            transforms.append(match_success_anim)

        return tuple(transforms)