# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
style match_tile_button is default:
    padding (16, 16)
    background Solid("#2b1c3d")
    hover_background Solid("#3e2556")
    selected_background Solid("#5b3580")
    xminimum 120
    yminimum 120

style match_tile_button_text is default:
    size 48
    color "#f3edff"

transform match_swap_anim(dx=0, dy=0):
    subpixel True
    xoffset dx
    yoffset dy
    easeout 0.18 xoffset 0 yoffset 0

transform match_success_anim:
    subpixel True
    linear 0.08 zoom 1.1
    linear 0.22 zoom 0.75 alpha 0.0

screen match_minigame():
    modal True
    tag menu
    zorder 200

    add Solid("#000000c8")

    if match_pending_resolution:
        timer 0.45 action Function(finalize_match_resolution)

    if match_swap_cells:
        timer 0.3 action Function(clear_match_swap_effect)

    if match_autoplay:
        timer 0.4 repeat True action Function(autoplay_step)

    frame:
        xalign 0.5
        yalign 0.5
        padding (32, 32)
        background Solid("#120b1c")

        vbox:
            spacing 18
            text "Sigil Array Trial" size 54
            text "Score: [match_score] / [match_target_score]" size 36
            text "Turns Remaining: [match_turns]" size 34
            text match_message size 28

            if match_board:
                grid match_board.size match_board.size spacing MATCH_TILE_SPACING:
                    for row in range(match_board.size):
                        for col in range(match_board.size):
                            $ tile = match_board.grid[row][col] or "?"
                            $ is_selected = match_selected_cell == (row, col)
                            $ tile_transforms = get_tile_transforms(row, col)
                            textbutton tile:
                                style_prefix "match_tile"
                                text_xalign 0.5
                                text_yalign 0.5
                                selected is_selected
                                at tile_transforms
                                action Function(handle_match_tile_click, row, col)
                                sensitive match_turns > 0 and not match_board_locked and not match_pending_resolution
            else:
                text "Preparing board..." size 32

            hbox:
                spacing 20
                textbutton "Reset Board" action Function(reset_match3_state)
                $ autoplay_label = "Autoplay: ON" if match_autoplay else "Autoplay: OFF"
                textbutton autoplay_label action Function(toggle_match_autoplay)
                if match_turns <= 0:
                    textbutton "Complete Trial" action Return(True)
                else:
                    textbutton "Concede" action Return(False)

label match_minigame:
    $ reset_match3_state()
    $ result = renpy.call_screen("match_minigame")
    return result