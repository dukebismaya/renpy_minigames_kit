# Copyright (c) 2025 Bismaya Jyoti Dalei. Licensed under the MIT License.
# Chess Saga Engine Created by Bismaya Jyoti Dalei.

default chess_state = None
default chess_ai_delay = 0.55

init -10 python:
    if not hasattr(config, "image_buttons"):
        config.image_buttons = None
    if not hasattr(config, "image_labels"):
        config.image_labels = None

init python:
    import math
    import random
    from dataclasses import dataclass
    from typing import List, Optional

    from renpy.display import im as renpy_im

    CHESS_TILE_SIZE = 108
    CHESS_TILE_SPACING = 6
    CHESS_BOARD_SIZE = CHESS_TILE_SIZE * 8 + CHESS_TILE_SPACING * 7
    CHESS_CAPTURE_ICON = 52
    CHESS_PIECE_SIZE = 96
    CHESS_HINT_LINE_WIDTH = 6
    CHESS_PROMOTION_CHOICES = ("queen", "rook", "bishop", "knight")
    CHESS_SEARCH_MAX = 100000
    CHESS_MATE_VALUE = 90000

    CHESS_ASSET_PATH = "minigames/chess_saga/assets/"

    def chess_asset(path):
        return CHESS_ASSET_PATH + path

    CHESS_THEMES = {
        "gray": {
            "label": "Obsidian Gray",
            "light_src": chess_asset("square gray light _png_128px.png"),
            "dark_src": chess_asset("square gray dark _png_128px.png"),
        },
        "brown": {
            "label": "Amberwood",
            "light_src": chess_asset("square brown light_png_128px.png"),
            "dark_src": chess_asset("square brown dark_png_128px.png"),
        },
    }

    for theme_data in CHESS_THEMES.values():
        theme_data["light_img"] = renpy_im.Scale(theme_data["light_src"], CHESS_TILE_SIZE, CHESS_TILE_SIZE)
        theme_data["dark_img"] = renpy_im.Scale(theme_data["dark_src"], CHESS_TILE_SIZE, CHESS_TILE_SIZE)

    PIECE_IMAGE_PATHS = {
        ("white", "king"): chess_asset("w_king_png_128px.png"),
        ("white", "queen"): chess_asset("w_queen_png_128px.png"),
        ("white", "rook"): chess_asset("w_rook_png_128px.png"),
        ("white", "bishop"): chess_asset("w_bishop_png_128px.png"),
        ("white", "knight"): chess_asset("w_knight_png_128px.png"),
        ("white", "pawn"): chess_asset("w_pawn_png_128px.png"),
        ("black", "king"): chess_asset("b_king_png_128px.png"),
        ("black", "queen"): chess_asset("b_queen_png_128px.png"),
        ("black", "rook"): chess_asset("b_rook_png_128px.png"),
        ("black", "bishop"): chess_asset("b_bishop_png_128px.png"),
        ("black", "knight"): chess_asset("b_knight_png_128px.png"),
        ("black", "pawn"): chess_asset("b_pawn_png_128px.png"),
    }

    CHESS_PIECE_IMAGES = {}
    for key, path in PIECE_IMAGE_PATHS.items():
        CHESS_PIECE_IMAGES[key] = renpy_im.Scale(path, CHESS_PIECE_SIZE, CHESS_PIECE_SIZE)

    def square_index(file_index, rank_index):
        return rank_index * 8 + file_index

    def square_coords(index):
        return (index % 8, index // 8)

    def square_in_bounds(file_index, rank_index):
        return 0 <= file_index < 8 and 0 <= rank_index < 8

    def mirror_index(index):
        file_index, rank_index = square_coords(index)
        return square_index(file_index, 7 - rank_index)

    KNIGHT_OFFSETS = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1),
    ]

    BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    KING_OFFSETS = BISHOP_DIRS + ROOK_DIRS

    PIECE_VALUES = {
        "pawn": 100,
        "knight": 320,
        "bishop": 330,
        "rook": 500,
        "queen": 900,
        "king": 20000,
    }

    CENTER_SQUARES = {27, 28, 35, 36}
    START_RANK_ORDER = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]

    class ChessPiece(object):

        def __init__(self, color, kind, moved=False):
            self.color = color
            self.kind = kind
            self.moved = moved

        def copy(self):
            return ChessPiece(self.color, self.kind, self.moved)

    @dataclass
    class ChessMove:
        from_square: int
        to_square: int
        color: str
        piece_kind: str
        promotion: Optional[str] = None
        castle_side: Optional[str] = None
        is_en_passant: bool = False
        en_passant_capture: Optional[int] = None
        en_passant_target: Optional[int] = None

        def key(self):
            return (self.from_square, self.to_square, self.promotion, self.castle_side, self.is_en_passant)

    class ChessState(object):
        def __init__(self):
            self.mode = "pvai"
            self.board_theme = "gray"
            self.hints_enabled = True
            self.ai_depth = 2
            self.reset_board(preserve_preferences=True)

        def reset_board(self, preserve_preferences=True):
            if not preserve_preferences:
                self.mode = "pvai"
                self.board_theme = "gray"
                self.hints_enabled = True
            self.board = [None] * 64
            for file_index, piece_name in enumerate(START_RANK_ORDER):
                self.board[square_index(file_index, 0)] = ChessPiece("white", piece_name)
                self.board[square_index(file_index, 1)] = ChessPiece("white", "pawn")
                self.board[square_index(file_index, 7)] = ChessPiece("black", piece_name)
                self.board[square_index(file_index, 6)] = ChessPiece("black", "pawn")
            self.to_move = "white"
            self.status_message = "White to move."
            self.selected_square = None
            self.available_moves = []
            self.last_move = None
            self.hint_lines = []
            self.capture_highlights = {"targets": set(), "color": None}
            self.threat_highlights = {"targets": set(), "color": None}
            self.captured_white = []
            self.captured_black = []
            self.checkmate = False
            self.stalemate = False
            self.awaiting_promotion_moves = None
            self.en_passant_square = None
            self.white_can_castle_k = True
            self.white_can_castle_q = True
            self.black_can_castle_k = True
            self.black_can_castle_q = True
            self.highlighted_king = None
            self.ai_pending = False
            self.legal_cache = None
            self.legal_cache_color = None
            self.move_counter = 1
            self.refresh_hint_lines()

        def clone(self):
            other = ChessState.__new__(ChessState)
            other.mode = self.mode
            other.board_theme = self.board_theme
            other.hints_enabled = self.hints_enabled
            other.ai_depth = self.ai_depth
            other.board = [piece.copy() if piece else None for piece in self.board]
            other.to_move = self.to_move
            other.status_message = self.status_message
            other.selected_square = None
            other.available_moves = []
            other.last_move = self.last_move
            other.hint_lines = []
            other.capture_highlights = {"targets": set(), "color": None}
            other.threat_highlights = {"targets": set(), "color": None}
            other.captured_white = list(self.captured_white)
            other.captured_black = list(self.captured_black)
            other.checkmate = self.checkmate
            other.stalemate = self.stalemate
            other.awaiting_promotion_moves = None
            other.en_passant_square = self.en_passant_square
            other.white_can_castle_k = self.white_can_castle_k
            other.white_can_castle_q = self.white_can_castle_q
            other.black_can_castle_k = self.black_can_castle_k
            other.black_can_castle_q = self.black_can_castle_q
            other.highlighted_king = self.highlighted_king
            other.ai_pending = self.ai_pending
            other.legal_cache = None
            other.legal_cache_color = None
            other.move_counter = self.move_counter
            return other

        def clear_selection(self):
            self.selected_square = None
            self.available_moves = []
            self.refresh_hint_lines()

        def refresh_hint_lines(self):
            if not self.hints_enabled or self.selected_square is None or not self.available_moves:
                self.hint_lines = []
                self.capture_highlights = {"targets": set(), "color": None}
            else:
                sx, sy = square_coords(self.selected_square)
                start_x = sx * (CHESS_TILE_SIZE + CHESS_TILE_SPACING) + CHESS_TILE_SIZE / 2
                start_y = (7 - sy) * (CHESS_TILE_SIZE + CHESS_TILE_SPACING) + CHESS_TILE_SIZE / 2
                lines = []
                for move in self.available_moves:
                    dx, dy = square_coords(move.to_square)
                    dest_x = dx * (CHESS_TILE_SIZE + CHESS_TILE_SPACING) + CHESS_TILE_SIZE / 2
                    dest_y = (7 - dy) * (CHESS_TILE_SIZE + CHESS_TILE_SPACING) + CHESS_TILE_SIZE / 2
                    length = math.hypot(dest_x - start_x, dest_y - start_y)
                    angle = math.degrees(math.atan2(dest_y - start_y, dest_x - start_x))
                    lines.append({
                        "center_x": (start_x + dest_x) / 2,
                        "center_y": (start_y + dest_y) / 2,
                        "length": length,
                        "angle": angle,
                    })
                self.hint_lines = lines
                self.capture_highlights = self._compute_capture_highlights()
            self._update_threat_highlights()

        def _compute_capture_highlights(self):
            if not self.hints_enabled or self.selected_square is None:
                return {"targets": set(), "color": None}
            captures = set()
            for move in self.available_moves:
                if move.is_en_passant and move.en_passant_capture is not None:
                    captures.add(move.en_passant_capture)
                else:
                    target_piece = self.board[move.to_square]
                    if target_piece and target_piece.color != move.color:
                        captures.add(move.to_square)
            return {"targets": captures, "color": self.to_move}

        def _update_threat_highlights(self):
            if not self.hints_enabled:
                self.threat_highlights = {"targets": set(), "color": None}
                return
            opponent = "white" if self.to_move == "black" else "black"
            threatened = set()
            for move in self._legal_moves_for_color(opponent):
                if move.is_en_passant and move.en_passant_capture is not None:
                    threatened.add(move.en_passant_capture)
                else:
                    target_piece = self.board[move.to_square]
                    if target_piece and target_piece.color != move.color:
                        threatened.add(move.to_square)
            self.threat_highlights = {"targets": threatened, "color": opponent}

        def set_mode(self, mode):
            if mode not in ("pvai", "pvp"):
                return
            if self.mode != mode:
                self.mode = mode
                self.reset_board(preserve_preferences=True)

        def set_theme(self, theme):
            if theme in CHESS_THEMES:
                self.board_theme = theme

        def toggle_hints(self):
            self.hints_enabled = not self.hints_enabled
            self.refresh_hint_lines()

        def resolve_promotion(self, choice):
            if not self.awaiting_promotion_moves:
                return
            for move in self.awaiting_promotion_moves:
                if move.promotion == choice:
                    self.apply_move(move)
                    self.awaiting_promotion_moves = None
                    return
            self.apply_move(self.awaiting_promotion_moves[0])
            self.awaiting_promotion_moves = None

        def _legal_moves_for_color(self, color):
            if self.legal_cache_color != color or self.legal_cache is None:
                self.legal_cache = self.generate_legal_moves(color)
                self.legal_cache_color = color
            return self.legal_cache

        def handle_click(self, square):
            if self.game_over():
                return
            if self.mode == "pvai" and self.to_move == "black":
                return
            if self.awaiting_promotion_moves:
                return
            if self.selected_square == square:
                self.clear_selection()
                return
            if self.selected_square is not None:
                candidates = [m for m in self.available_moves if m.to_square == square]
                if candidates:
                    if len(candidates) == 1:
                        self.apply_move(candidates[0])
                    else:
                        self.awaiting_promotion_moves = candidates
                        self.status_message = "Pick a piece for promotion."
                    return
            piece = self.board[square]
            if piece and piece.color == self.to_move:
                moves = [m for m in self._legal_moves_for_color(self.to_move) if m.from_square == square]
                self.selected_square = square
                self.available_moves = moves
                self.refresh_hint_lines()
                return
            self.clear_selection()

        def game_over(self):
            return self.checkmate or self.stalemate

        def schedule_ai_if_needed(self):
            if self.should_ai_move():
                self.ai_pending = True
            else:
                self.ai_pending = False

        def should_ai_move(self):
            return self.mode == "pvai" and self.to_move == "black" and not self.game_over() and self.awaiting_promotion_moves is None

        def ai_step(self):
            if not self.should_ai_move():
                self.ai_pending = False
                return
            move = self.pick_ai_move()
            if move:
                self.apply_move(move, skip_ai_schedule=True)
            else:
                self.stalemate = True
                self.status_message = "Draw - the AI has no moves."
            self.ai_pending = False

        def apply_move(self, move, skip_ai_schedule=False):
            self._apply_move_internal(move, advance_turn=True, record_capture=True)
            self.awaiting_promotion_moves = None
            self.clear_selection()
            self._after_move_update(move)
            if not skip_ai_schedule:
                self.schedule_ai_if_needed()
            else:
                if self.mode != "pvai" or self.to_move != "black":
                    self.ai_pending = False

        def _after_move_update(self, move):
            mover = move.color
            opponent = "white" if mover == "black" else "black"
            self.highlighted_king = None
            legal = self.generate_legal_moves(opponent)
            if not legal:
                if self.is_in_check(opponent):
                    self.status_message = "Checkmate! {} wins.".format(mover.capitalize())
                    self.checkmate = True
                    self.stalemate = False
                else:
                    self.status_message = "Stalemate. The duel is balanced."
                    self.checkmate = False
                    self.stalemate = True
            else:
                self.checkmate = False
                self.stalemate = False
                if self.is_in_check(opponent):
                    self.status_message = "{} in check!".format(opponent.capitalize())
                    self.highlighted_king = self.king_square(opponent)
                else:
                    if self.mode == "pvai" and opponent == "black":
                        self.status_message = "AI preparing a countermove."
                    else:
                        self.status_message = "{} to move.".format(opponent.capitalize())
            self.last_move = (move.from_square, move.to_square)
            self.move_counter += 1
            self.legal_cache = None
            self.legal_cache_color = None

        def _apply_move_internal(self, move, advance_turn=True, record_capture=True):
            piece = self.board[move.from_square]
            if piece is None:
                return
            original_kind = piece.kind
            captured_piece = None
            if move.is_en_passant and move.en_passant_capture is not None:
                captured_piece = self.board[move.en_passant_capture]
                self.board[move.en_passant_capture] = None
            else:
                captured_piece = self.board[move.to_square]
            self.board[move.to_square] = piece
            self.board[move.from_square] = None
            if move.promotion:
                piece.kind = move.promotion
            piece.moved = True
            if captured_piece and record_capture:
                if captured_piece.color == "white":
                    self.captured_white.append(captured_piece.kind)
                else:
                    self.captured_black.append(captured_piece.kind)
            if move.castle_side:
                self._move_castle_rook(move)
            self.en_passant_square = move.en_passant_target
            self._update_castling_rights(move, original_kind, captured_piece)
            if advance_turn:
                self.to_move = "white" if move.color == "black" else "black"

        def _move_castle_rook(self, move):
            rank = 0 if move.color == "white" else 7
            if move.castle_side == "k":
                rook_from = square_index(7, rank)
                rook_to = square_index(5, rank)
            else:
                rook_from = square_index(0, rank)
                rook_to = square_index(3, rank)
            rook_piece = self.board[rook_from]
            if rook_piece:
                self.board[rook_from] = None
                self.board[rook_to] = rook_piece
                rook_piece.moved = True

        def _update_castling_rights(self, move, original_kind, captured_piece):
            if original_kind == "king":
                if move.color == "white":
                    self.white_can_castle_k = False
                    self.white_can_castle_q = False
                else:
                    self.black_can_castle_k = False
                    self.black_can_castle_q = False
            elif original_kind == "rook":
                if move.from_square == square_index(0, 0):
                    self.white_can_castle_q = False
                elif move.from_square == square_index(7, 0):
                    self.white_can_castle_k = False
                elif move.from_square == square_index(0, 7):
                    self.black_can_castle_q = False
                elif move.from_square == square_index(7, 7):
                    self.black_can_castle_k = False
            if captured_piece and captured_piece.kind == "rook":
                capture_square = move.en_passant_capture if move.is_en_passant else move.to_square
                if capture_square == square_index(0, 0):
                    self.white_can_castle_q = False
                elif capture_square == square_index(7, 0):
                    self.white_can_castle_k = False
                elif capture_square == square_index(0, 7):
                    self.black_can_castle_q = False
                elif capture_square == square_index(7, 7):
                    self.black_can_castle_k = False

        def generate_legal_moves(self, color):
            legal = []
            for move in self.generate_pseudo_moves(color):
                clone = self.clone()
                clone._apply_move_internal(move, advance_turn=True, record_capture=False)
                if not clone.is_in_check(color):
                    legal.append(move)
            return legal

        def generate_pseudo_moves(self, color):
            moves = []
            for index, piece in enumerate(self.board):
                if not piece or piece.color != color:
                    continue
                if piece.kind == "pawn":
                    moves.extend(self._pawn_moves(index, piece))
                elif piece.kind == "knight":
                    moves.extend(self._knight_moves(index, piece))
                elif piece.kind == "bishop":
                    moves.extend(self._slide_moves(index, piece, BISHOP_DIRS))
                elif piece.kind == "rook":
                    moves.extend(self._slide_moves(index, piece, ROOK_DIRS))
                elif piece.kind == "queen":
                    moves.extend(self._slide_moves(index, piece, BISHOP_DIRS + ROOK_DIRS))
                elif piece.kind == "king":
                    moves.extend(self._king_moves(index, piece))
            return moves

        def _pawn_moves(self, square, piece):
            moves = []
            file_index, rank_index = square_coords(square)
            direction = 1 if piece.color == "white" else -1
            start_rank = 1 if piece.color == "white" else 6
            forward_rank = rank_index + direction
            if square_in_bounds(file_index, forward_rank):
                forward_square = square_index(file_index, forward_rank)
                if self.board[forward_square] is None:
                    moves.extend(self._build_pawn_move(square, forward_square, piece))
                    if rank_index == start_rank:
                        two_rank = rank_index + (2 * direction)
                        two_square = square_index(file_index, two_rank)
                        if self.board[two_square] is None:
                            moves.append(ChessMove(
                                from_square=square,
                                to_square=two_square,
                                color=piece.color,
                                piece_kind=piece.kind,
                                en_passant_target=square_index(file_index, rank_index + direction),
                            ))
            for file_delta in (-1, 1):
                capture_file = file_index + file_delta
                capture_rank = rank_index + direction
                if not square_in_bounds(capture_file, capture_rank):
                    continue
                capture_square = square_index(capture_file, capture_rank)
                target_piece = self.board[capture_square]
                if target_piece and target_piece.color != piece.color:
                    moves.extend(self._build_pawn_move(square, capture_square, piece))
                elif self.en_passant_square == capture_square:
                    moves.append(ChessMove(
                        from_square=square,
                        to_square=capture_square,
                        color=piece.color,
                        piece_kind=piece.kind,
                        is_en_passant=True,
                        en_passant_capture=square_index(capture_file, rank_index),
                    ))
            return moves

        def _build_pawn_move(self, start, dest, piece):
            moves = []
            _, dest_rank = square_coords(dest)
            promotion_rank = 7 if piece.color == "white" else 0
            if dest_rank == promotion_rank:
                for kind in CHESS_PROMOTION_CHOICES:
                    moves.append(ChessMove(start, dest, piece.color, piece.kind, promotion=kind))
            else:
                moves.append(ChessMove(start, dest, piece.color, piece.kind))
            return moves

        def _knight_moves(self, square, piece):
            moves = []
            file_index, rank_index = square_coords(square)
            for dx, dy in KNIGHT_OFFSETS:
                nf = file_index + dx
                nr = rank_index + dy
                if not square_in_bounds(nf, nr):
                    continue
                target_index = square_index(nf, nr)
                target_piece = self.board[target_index]
                if target_piece is None or target_piece.color != piece.color:
                    moves.append(ChessMove(square, target_index, piece.color, piece.kind))
            return moves

        def _slide_moves(self, square, piece, directions):
            moves = []
            file_index, rank_index = square_coords(square)
            for dx, dy in directions:
                nf = file_index + dx
                nr = rank_index + dy
                while square_in_bounds(nf, nr):
                    target_index = square_index(nf, nr)
                    target_piece = self.board[target_index]
                    if target_piece is None:
                        moves.append(ChessMove(square, target_index, piece.color, piece.kind))
                    else:
                        if target_piece.color != piece.color:
                            moves.append(ChessMove(square, target_index, piece.color, piece.kind))
                        break
                    nf += dx
                    nr += dy
            return moves

        def _king_moves(self, square, piece):
            moves = []
            file_index, rank_index = square_coords(square)
            for dx, dy in KING_OFFSETS:
                nf = file_index + dx
                nr = rank_index + dy
                if not square_in_bounds(nf, nr):
                    continue
                target_index = square_index(nf, nr)
                target_piece = self.board[target_index]
                if target_piece is None or target_piece.color != piece.color:
                    moves.append(ChessMove(square, target_index, piece.color, piece.kind))
            moves.extend(self._castle_moves(square, piece))
            return moves

        def _castle_moves(self, square, piece):
            moves = []
            if piece.moved or self.is_in_check(piece.color):
                return moves
            rank = 0 if piece.color == "white" else 7
            if piece.color == "white" and self.white_can_castle_k and self._castle_path_clear(square, "k"):
                moves.append(ChessMove(square, square_index(6, rank), piece.color, piece.kind, castle_side="k"))
            if piece.color == "white" and self.white_can_castle_q and self._castle_path_clear(square, "q"):
                moves.append(ChessMove(square, square_index(2, rank), piece.color, piece.kind, castle_side="q"))
            if piece.color == "black" and self.black_can_castle_k and self._castle_path_clear(square, "k"):
                moves.append(ChessMove(square, square_index(6, rank), piece.color, piece.kind, castle_side="k"))
            if piece.color == "black" and self.black_can_castle_q and self._castle_path_clear(square, "q"):
                moves.append(ChessMove(square, square_index(2, rank), piece.color, piece.kind, castle_side="q"))
            return moves

        def _castle_path_clear(self, square, side):
            piece = self.board[square]
            if piece is None or piece.kind != "king":
                return False
            rank = 0 if piece.color == "white" else 7
            opponent = "white" if piece.color == "black" else "black"
            file_index, _ = square_coords(square)
            if side == "k":
                rook_square = square_index(7, rank)
                path_files = [file_index + 1, file_index + 2]
                king_files = [file_index + 1, file_index + 2]
            else:
                rook_square = square_index(0, rank)
                path_files = [file_index - 1, file_index - 2, file_index - 3]
                king_files = [file_index - 1, file_index - 2]
            rook_piece = self.board[rook_square]
            if not rook_piece or rook_piece.kind != "rook" or rook_piece.color != piece.color or rook_piece.moved:
                return False
            for f in path_files:
                if not square_in_bounds(f, rank):
                    return False
                if self.board[square_index(f, rank)] is not None:
                    return False
            for f in king_files:
                if self.is_square_attacked(square_index(f, rank), opponent):
                    return False
            return True

        def king_square(self, color):
            for idx, piece in enumerate(self.board):
                if piece and piece.color == color and piece.kind == "king":
                    return idx
            return None

        def is_in_check(self, color):
            king_sq = self.king_square(color)
            if king_sq is None:
                return False
            opponent = "white" if color == "black" else "black"
            return self.is_square_attacked(king_sq, opponent)

        def is_square_attacked(self, square, by_color):
            file_index, rank_index = square_coords(square)
            pawn_dir = 1 if by_color == "white" else -1
            for df in (-1, 1):
                af = file_index + df
                ar = rank_index - pawn_dir
                if square_in_bounds(af, ar):
                    attacker = self.board[square_index(af, ar)]
                    if attacker and attacker.color == by_color and attacker.kind == "pawn":
                        return True
            for dx, dy in KNIGHT_OFFSETS:
                nf = file_index + dx
                nr = rank_index + dy
                if square_in_bounds(nf, nr):
                    attacker = self.board[square_index(nf, nr)]
                    if attacker and attacker.color == by_color and attacker.kind == "knight":
                        return True
            for dx, dy in BISHOP_DIRS:
                nf = file_index + dx
                nr = rank_index + dy
                while square_in_bounds(nf, nr):
                    attacker = self.board[square_index(nf, nr)]
                    if attacker:
                        if attacker.color == by_color and attacker.kind in ("bishop", "queen"):
                            return True
                        break
                    nf += dx
                    nr += dy
            for dx, dy in ROOK_DIRS:
                nf = file_index + dx
                nr = rank_index + dy
                while square_in_bounds(nf, nr):
                    attacker = self.board[square_index(nf, nr)]
                    if attacker:
                        if attacker.color == by_color and attacker.kind in ("rook", "queen"):
                            return True
                        break
                    nf += dx
                    nr += dy
            for dx, dy in KING_OFFSETS:
                nf = file_index + dx
                nr = rank_index + dy
                if square_in_bounds(nf, nr):
                    attacker = self.board[square_index(nf, nr)]
                    if attacker and attacker.color == by_color and attacker.kind == "king":
                        return True
            return False

        def pick_ai_move(self):
            moves = self.generate_legal_moves("black")
            if not moves:
                return None
            random.shuffle(moves)
            best_move = moves[0]
            best_score = CHESS_SEARCH_MAX
            for move in moves:
                clone = self.clone()
                clone._apply_move_internal(move, advance_turn=True, record_capture=False)
                score = clone._search(self.ai_depth - 1, -CHESS_SEARCH_MAX, CHESS_SEARCH_MAX)
                if score < best_score:
                    best_score = score
                    best_move = move
            return best_move

        def _search(self, depth, alpha, beta):
            if depth <= 0:
                return self.evaluate()
            moves = self.generate_legal_moves(self.to_move)
            if not moves:
                if self.is_in_check(self.to_move):
                    if self.to_move == "white":
                        return -CHESS_MATE_VALUE + depth
                    return CHESS_MATE_VALUE - depth
                return 0
            if self.to_move == "white":
                value = -CHESS_SEARCH_MAX
                for move in moves:
                    clone = self.clone()
                    clone._apply_move_internal(move, advance_turn=True, record_capture=False)
                    score = clone._search(depth - 1, alpha, beta)
                    value = max(value, score)
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
                return value
            value = CHESS_SEARCH_MAX
            for move in moves:
                clone = self.clone()
                clone._apply_move_internal(move, advance_turn=True, record_capture=False)
                score = clone._search(depth - 1, alpha, beta)
                value = min(value, score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

        def evaluate(self):
            score = 0
            for index, piece in enumerate(self.board):
                if not piece:
                    continue
                value = PIECE_VALUES[piece.kind]
                if index in CENTER_SQUARES and piece.kind != "king":
                    value += 12
                file_index, rank_index = square_coords(index)
                advancement = rank_index if piece.color == "white" else (7 - rank_index)
                if piece.kind == "pawn":
                    value += advancement * 2
                if piece.color == "white":
                    score += value
                else:
                    score -= value
            return score

    def chess_get_or_create_state():
        global chess_state
        if chess_state is None:
            chess_state = ChessState()
        return chess_state

    def chess_prepare_state():
        state = chess_get_or_create_state()
        state.reset_board(preserve_preferences=True)
        return state

    def chess_click_square(index):
        state = chess_get_or_create_state()
        state.handle_click(index)

    def chess_reset_game():
        state = chess_get_or_create_state()
        state.reset_board(preserve_preferences=True)

    def chess_set_mode(mode):
        state = chess_get_or_create_state()
        state.set_mode(mode)
        state.schedule_ai_if_needed()

    def chess_set_theme(theme):
        state = chess_get_or_create_state()
        state.set_theme(theme)

    def chess_toggle_hints():
        state = chess_get_or_create_state()
        state.toggle_hints()

    def chess_resolve_promotion(choice):
        state = chess_get_or_create_state()
        state.resolve_promotion(choice)

    def chess_ai_step():
        state = chess_get_or_create_state()
        state.ai_step()