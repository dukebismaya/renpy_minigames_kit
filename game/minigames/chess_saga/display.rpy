# Copyright (c) 2025 Bismaya Jyoti Dalei. Licensed under the MIT License.

style chess_tile_button is default:
    padding (0, 0)
    background None
    hover_background None

screen chess_captured_panel(pieces, title, piece_color):
    frame:
        background Solid("#101520")
        padding (10, 10)
        xsize 200
        vbox:
            spacing 6
            text title size 24
            if pieces:
                $ rows = max(1, int((len(pieces) + 3) / 4.0))
                grid 4 rows:
                    for kind in pieces:
                        $ img = CHESS_PIECE_IMAGES.get((piece_color, kind))
                        if img:
                            add Transform(img, zoom=CHESS_CAPTURE_ICON / float(CHESS_PIECE_SIZE))
                        else:
                            null
            else:
                text "None" size 18 color "#8da2c0"

screen chess_promotion_overlay(moves):
    modal True
    zorder 400
    add Solid("#000000a6")
    frame:
        xalign 0.5
        yalign 0.5
        padding (26, 24)
        background Solid("#1a1f2b")
        vbox:
            spacing 16
            text "Choose promotion" size 38
            $ options = [m.promotion for m in moves]
            hbox:
                spacing 12
                for choice in CHESS_PROMOTION_CHOICES:
                    if choice in options:
                        $ img = CHESS_PIECE_IMAGES.get((moves[0].color, choice))
                        button:
                            background Solid("#232a39")
                            hover_background Solid("#323b4f")
                            padding (16, 12)
                            action Function(chess_resolve_promotion, choice)
                            has vbox:
                                spacing 6
                                xalign 0.5
                                text choice.capitalize() xalign 0.5
                                if img:
                                    add Transform(img, zoom=0.6, xalign=0.5)

screen chess_saga_minigame():
    modal True
    tag menu

    $ state = chess_get_or_create_state()

    add Solid("#05070ccc")

    if state.should_ai_move() and state.ai_pending:
        timer chess_ai_delay action Function(chess_ai_step)

    frame:
        xalign 0.5
        yalign 0.5
        padding (32, 30)
        background Solid("#0b0f18f0")
        vbox:
            spacing 18
            text "Chess Saga" size 58
            text state.status_message size 30 color "#d4e4ff"
            hbox:
                spacing 28
                vbox:
                    spacing 12
                    use chess_captured_panel(state.captured_black, "Captured (White)", "black")
                    use chess_captured_panel(state.captured_white, "Captured (Black)", "white")
                fixed:
                    xsize CHESS_BOARD_SIZE
                    ysize CHESS_BOARD_SIZE
                    $ board_theme = CHESS_THEMES[state.board_theme]
                    $ highlight_targets = [m.to_square for m in state.available_moves]
                    $ capture_info = state.capture_highlights or {"targets": set(), "color": None}
                    $ threat_info = state.threat_highlights or {"targets": set(), "color": None}
                    $ last_move_squares = state.last_move if state.last_move else ()
                    $ disabled = state.game_over() or (state.mode == "pvai" and state.to_move == "black") or state.awaiting_promotion_moves
                    grid 8 8 spacing CHESS_TILE_SPACING:
                        for rank in range(7, -1, -1):
                            for file_index in range(8):
                                $ idx = square_index(file_index, rank)
                                $ base_img = board_theme["light_img"] if (file_index + rank) % 2 == 0 else board_theme["dark_img"]
                                $ piece = state.board[idx]
                                button:
                                    style "chess_tile_button"
                                    xsize CHESS_TILE_SIZE
                                    ysize CHESS_TILE_SIZE
                                    background base_img
                                    hover_background base_img
                                    action Function(chess_click_square, idx)
                                    sensitive not disabled
                                    if idx in last_move_squares:
                                        add Solid("#ffd9603c")
                                    if state.highlighted_king == idx:
                                        add Solid("#ff4f4f5c")
                                    if state.selected_square == idx:
                                        add Solid("#f5ffb24a")
                                    elif state.hints_enabled and idx in highlight_targets:
                                        add Solid("#e3ff7533")
                                    if state.hints_enabled and idx in threat_info["targets"]:
                                        $ threat_color = "#ff5c5c48" if threat_info["color"] == "white" else "#ff7bff3c"
                                        add Solid(threat_color)
                                    if state.hints_enabled and idx in capture_info["targets"]:
                                        $ capture_color = "#ffa45a4c" if capture_info["color"] == "white" else "#ffde5a4c"
                                        add Solid(capture_color)
                                    if piece:
                                        $ img = CHESS_PIECE_IMAGES.get((piece.color, piece.kind))
                                        if img:
                                            add Transform(img, xalign=0.5, yalign=0.5)
                    if state.hint_lines:
                        for line in state.hint_lines:
                            add Transform(
                                Solid("#f8ff876e", xsize=int(line["length"]), ysize=CHESS_HINT_LINE_WIDTH),
                                xanchor=0.5,
                                yanchor=0.5,
                                xpos=line["center_x"],
                                ypos=line["center_y"],
                                rotate=line["angle"],
                            )
                vbox:
                    spacing 10
                    frame:
                        background Solid("#131a26")
                        padding (12, 12)
                        vbox:
                            spacing 10
                            text "Modes" size 28
                            textbutton "Player vs AI":
                                action Function(chess_set_mode, "pvai")
                                selected state.mode == "pvai"
                            textbutton "Player vs Player":
                                action Function(chess_set_mode, "pvp")
                                selected state.mode == "pvp"
                    frame:
                        background Solid("#131a26")
                        padding (12, 12)
                        vbox:
                            spacing 10
                            text "Boards" size 28
                            for theme_id, theme_info in CHESS_THEMES.items():
                                textbutton theme_info["label"]:
                                    action Function(chess_set_theme, theme_id)
                                    selected state.board_theme == theme_id
                    frame:
                        background Solid("#131a26")
                        padding (12, 12)
                        vbox:
                            spacing 10
                            text "Options" size 28
                            textbutton ("Hints: ON" if state.hints_enabled else "Hints: OFF") action Function(chess_toggle_hints)
                            textbutton "Reset Board" action Function(chess_reset_game)
                            textbutton "Exit" action Return(False)
            if state.game_over():
                text "Tap reset to start another match." size 24 color "#cdd8ff"

    if state.awaiting_promotion_moves:
        use chess_promotion_overlay(state.awaiting_promotion_moves)

label chess_saga_minigame:
    $ chess_prepare_state()
    $ renpy.call_screen("chess_saga_minigame")
    return
