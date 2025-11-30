# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
default snake_grid_size = 9
default snake_segments = []
default snake_direction = "right"
default snake_pending_direction = None
default snake_food = None
default snake_running = False
default snake_dead = False
default snake_score = 0
default snake_high_score = 0
default snake_message = "Use arrows to guide the serpent."
default snake_tick_delay = 0.35

init python:
    import random

    SNAKE_DIR_VECTORS = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }
    SNAKE_OPPOSITES = {
        "up": "down",
        "down": "up",
        "left": "right",
        "right": "left",
    }

    def reset_snake_game():
        global snake_segments, snake_direction, snake_pending_direction
        global snake_food, snake_running, snake_dead, snake_score, snake_message
        center = snake_grid_size // 2
        snake_segments = [
            (center, center - 1),
            (center, center - 2),
        ]
        snake_direction = "right"
        snake_pending_direction = None
        snake_score = 0
        snake_dead = False
        snake_running = True
        snake_message = "Use arrows to guide the serpent."
        spawn_snake_food()

    def spawn_snake_food():
        global snake_food
        all_cells = [
            (row, col)
            for row in range(snake_grid_size)
            for col in range(snake_grid_size)
        ]
        candidates = [cell for cell in all_cells if cell not in snake_segments]
        snake_food = random.choice(candidates) if candidates else None

    def set_snake_direction(direction):
        global snake_pending_direction
        if not snake_running or snake_dead:
            return
        if direction == snake_direction or direction == snake_pending_direction:
            return
        if SNAKE_OPPOSITES[direction] == snake_direction:
            return
        snake_pending_direction = direction

    def snake_step():
        global snake_segments, snake_direction, snake_pending_direction
        global snake_food, snake_running, snake_dead, snake_score, snake_high_score
        global snake_message
        if not snake_running or snake_dead:
            return

        if snake_pending_direction:
            snake_direction = snake_pending_direction
            snake_pending_direction = None

        dr, dc = SNAKE_DIR_VECTORS[snake_direction]
        head_r, head_c = snake_segments[0]
        new_head = (head_r + dr, head_c + dc)

        if (
            new_head[0] < 0
            or new_head[0] >= snake_grid_size
            or new_head[1] < 0
            or new_head[1] >= snake_grid_size
            or new_head in snake_segments
        ):
            snake_running = False
            snake_dead = True
            snake_message = "The serpent crashed!"
            snake_high_score = max(snake_high_score, snake_score)
            return

        snake_segments.insert(0, new_head)

        if snake_food and new_head == snake_food:
            snake_score += 5
            spawn_snake_food()
            snake_message = "Snacked on a rune shard!"
        else:
            snake_segments.pop()

        if snake_food is None:
            snake_running = False
            snake_dead = True
            snake_message = "Perfect run!"
            snake_high_score = max(snake_high_score, snake_score)

    def toggle_snake_running():
        global snake_running, snake_dead, snake_message
        if snake_dead:
            return
        snake_running = not snake_running
        snake_message = "Paused." if not snake_running else "Keep slithering."

    def restart_snake_game():
        reset_snake_game()

style snake_tile_button is default:
    padding (6, 6)
    background Solid("#1b232f")
    hover_background Solid("#1b232f")
    insensitive_background Solid("#1b232f")
    xminimum 48
    yminimum 48

style snake_tile_button_text is default:
    size 28
    color "#7fc2ff"
    text_align 0.5

screen snake_minigame():
    modal True
    tag menu
    zorder 200

    add Solid("#000000c8")

    if snake_running and not snake_dead:
        timer snake_tick_delay repeat True action Function(snake_step)

    key "K_UP" action Function(set_snake_direction, "up")
    key "K_DOWN" action Function(set_snake_direction, "down")
    key "K_LEFT" action Function(set_snake_direction, "left")
    key "K_RIGHT" action Function(set_snake_direction, "right")
    key "w" action Function(set_snake_direction, "up")
    key "s" action Function(set_snake_direction, "down")
    key "a" action Function(set_snake_direction, "left")
    key "d" action Function(set_snake_direction, "right")

    frame:
        xalign 0.5
        yalign 0.5
        padding (32, 32)
        background Solid("#101722")

        vbox:
            spacing 18
            text "Serpent Run" size 54
            text "Score: [snake_score]   Best: [snake_high_score]" size 32
            text snake_message size 28

            grid snake_grid_size snake_grid_size spacing 6:
                for row in range(snake_grid_size):
                    for col in range(snake_grid_size):
                        $ cell = (row, col)
                        $ char = "·"
                        $ tile_bg = Solid("#1f2a39")
                        if snake_food and cell == snake_food:
                            $ char = "*"
                            $ tile_bg = Solid("#f8d86a")
                        elif snake_segments and cell == snake_segments[0]:
                            $ char = "@"
                            $ tile_bg = Solid("#6fe3a2")
                        elif cell in snake_segments:
                            $ char = "o"
                            $ tile_bg = Solid("#3fb97d")
                        textbutton char:
                            style_prefix "snake_tile"
                            background tile_bg
                            text_xalign 0.5
                            text_yalign 0.5
                            action NullAction()
                            sensitive False

            hbox:
                spacing 20
                $ pause_label = "Resume" if not snake_running and not snake_dead else "Pause"
                textbutton pause_label action Function(toggle_snake_running) sensitive (not snake_dead)
                textbutton "Restart" action Function(restart_snake_game)
                textbutton "Exit" action Return(False)

label snake_minigame:
    $ reset_snake_game()
    $ renpy.call_screen("snake_minigame")
    return
