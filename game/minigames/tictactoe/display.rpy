# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
default ttt_board = [None] * 9
default ttt_current_player = "X"
default ttt_game_over = False
default ttt_message = "Place a sigil to begin."
default ttt_vs_ai = True
default ttt_human_symbol = "X"
default ttt_ai_symbol = "O"
default ttt_last_winner = None
default ttt_winning_cells = []

default ttt_ai_delay = 0.45

init python:
    import random
    TTT_TILE_SIZE = 140
    TTT_TILE_SPACING = 14
    TTT_BOARD_SIZE = TTT_TILE_SIZE * 3 + TTT_TILE_SPACING * 2

    def ttt_winning_lines():
        return [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]

    def reset_ttt_game():
        global ttt_board, ttt_current_player, ttt_game_over, ttt_message
        global ttt_last_winner, ttt_winning_cells
        ttt_board = [None] * 9
        ttt_current_player = "X"
        ttt_game_over = False
        ttt_message = "Place a sigil to begin."
        ttt_last_winner = None
        ttt_winning_cells = []

    def set_ttt_mode(vs_ai):
        global ttt_vs_ai, ttt_message
        ttt_vs_ai = vs_ai
        reset_ttt_game()
        if vs_ai:
            ttt_message = "You are X. The seer AI counters with O."
        else:
            ttt_message = "Pass the device for two-player mode."

    def ttt_available_moves():
        return [i for i, cell in enumerate(ttt_board) if cell is None]

    def ttt_check_game_state(record=False):
        global ttt_winning_cells
        for idx, line in enumerate(ttt_winning_lines()):
            a, b, c = line
            if ttt_board[a] and ttt_board[a] == ttt_board[b] == ttt_board[c]:
                if record:
                    ttt_winning_cells = list(line)
                return ttt_board[a]
        if all(cell is not None for cell in ttt_board):
            if record:
                ttt_winning_cells = []
            return "draw"
        if record:
            ttt_winning_cells = []
        return None

    def ttt_finish_game(result):
        global ttt_game_over, ttt_message, ttt_last_winner
        ttt_game_over = True
        if result == "draw":
            ttt_message = "Stalemate. The ward stands."
        elif result:
            ttt_message = "{} claims the board.".format(result)
            ttt_last_winner = result

    def ttt_swap_player():
        global ttt_current_player
        ttt_current_player = "O" if ttt_current_player == "X" else "X"

    def play_ttt_move(index, from_ai=False):
        global ttt_message
        if ttt_game_over or ttt_board[index] is not None:
            return
        ttt_board[index] = ttt_current_player
        result = ttt_check_game_state(record=True)
        if result:
            ttt_finish_game(result)
            return
        ttt_swap_player()
        if ttt_vs_ai and ttt_current_player == ttt_ai_symbol and not from_ai:
            ttt_message = "AI plotting..."
        else:
            ttt_message = "{} to act.".format(ttt_current_player)

    def best_ttt_move(symbol):
        opponent = "O" if symbol == "X" else "X"
        # Win
        for idx in ttt_available_moves():
            ttt_board[idx] = symbol
            if ttt_check_game_state() == symbol:
                ttt_board[idx] = None
                return idx
            ttt_board[idx] = None
        # Block opponent
        for idx in ttt_available_moves():
            ttt_board[idx] = opponent
            if ttt_check_game_state() == opponent:
                ttt_board[idx] = None
                return idx
            ttt_board[idx] = None
        # Center, corners, sides
        for preferred in [4, 0, 2, 6, 8, 1, 3, 5, 7]:
            if preferred in ttt_available_moves():
                return preferred
        moves = ttt_available_moves()
        return random.choice(moves) if moves else None

    def ttt_ai_step():
        if not ttt_vs_ai or ttt_game_over or ttt_current_player != ttt_ai_symbol:
            return
        idx = best_ttt_move(ttt_ai_symbol)
        if idx is None:
            return
        play_ttt_move(idx, from_ai=True)
        if not ttt_game_over:
            ttt_message = "Your turn."


style ttt_tile_button is default:
    padding (12, 12)
    background Solid("#1b1f27")
    hover_background Solid("#272f3e")
    insensitive_background Solid("#1b1f27")
    xsize TTT_TILE_SIZE
    ysize TTT_TILE_SIZE

style ttt_tile_button_text is default:
    size 72
    color "#f5f5f5"
    outlines [(2, "#0c0c0c", 0, 0)]

style ttt_tile_button_hover is ttt_tile_button

style ttt_tile_button_hover_text is ttt_tile_button_text

transform ttt_win_flash:
    on show:
        alpha 0.6
    linear 0.25 alpha 1.0
    linear 0.25 alpha 0.6
    repeat

screen tic_tac_toe_minigame():
    modal True
    tag menu
    zorder 200

    add Solid("#000000c8")

    if ttt_vs_ai and not ttt_game_over and ttt_current_player == ttt_ai_symbol:
        timer ttt_ai_delay action Function(ttt_ai_step)

    frame:
        xalign 0.5
        yalign 0.5
        padding (36, 36)
        background Solid("#121822")

        vbox:
            spacing 18
            text "Sigil Grid: Tic-Tac Trials" size 54
            text ttt_message size 30

            fixed:
                clipping True
                xsize TTT_BOARD_SIZE
                ysize TTT_BOARD_SIZE

                grid 3 3 spacing TTT_TILE_SPACING:
                    for index in range(9):
                        $ token = ttt_board[index] or ""
                        $ tile_bg = Solid("#1b1f27")
                        if index in ttt_winning_cells:
                            $ tile_bg = Solid("#ffb4b4")
                        $ cell_available = (not ttt_game_over and ttt_board[index] is None and (not ttt_vs_ai or ttt_current_player == ttt_human_symbol))
                        textbutton token:
                            style_prefix "ttt_tile"
                            background tile_bg
                            text_xalign 0.5 
                            text_yalign 0.5
                            action Function(play_ttt_move, index)
                            sensitive cell_available
                            if cell_available:
                                hover_background Solid("#2d3647")
                            else:
                                hover_background tile_bg
                            if index in ttt_winning_cells:
                                at ttt_win_flash


            hbox:
                spacing 20
                textbutton "Reset" action Function(reset_ttt_game)
                textbutton "Vs AI" action Function(set_ttt_mode, True)
                textbutton "2 Player" action Function(set_ttt_mode, False)
                textbutton "Exit" action Return(False)

label tic_tac_toe_minigame:
    $ reset_ttt_game()
    $ renpy.call_screen("tic_tac_toe_minigame")
    return
