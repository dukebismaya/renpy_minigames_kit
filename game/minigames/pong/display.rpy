# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
default pong_left_score = 0
default pong_right_score = 0
default pong_ball_x = 0.5
default pong_ball_y = 0.5
default pong_ball_vx = 0.4
default pong_ball_vy = 0.2
default pong_paddle_left_y = 0.5
default pong_paddle_right_y = 0.5
default pong_running = True
default pong_message = "W/S to move the left paddle."
default pong_last_point = None
default pong_target_score = 7
default pong_paused = False

default pong_tick_delay = 0.02

default pong_ai_enabled = True

default pong_last_winner = None
default pong_mode = "player_vs_ai"
default pong_right_manual_override = False
default pong_left_velocity = 0.0
default pong_right_velocity = 0.0

init python:
    import math
    import random
    import renpy.pygame as pygame
    import renpy.display.render as ren_render
    import renpy.display.pgrender as ren_pgrender
    from renpy.color import Color

    PONG_FIELD_WIDTH = 900
    PONG_FIELD_HEIGHT = 520
    PONG_PADDLE_HEIGHT = 0.18
    PONG_PADDLE_WIDTH = 0.02
    PONG_PADDLE_SPEED = 1.3
    PONG_PADDLE_ACCEL = 8.0
    PONG_BALL_RADIUS = 0.02
    PONG_DT = 0.02
    PONG_AI_SPEED = 0.35

    def _color_to_rgba_tuple(color_value):
        rgba = Color(color_value).rgba
        return (
            int(rgba[0] * 255),
            int(rgba[1] * 255),
            int(rgba[2] * 255),
            int(rgba[3] * 255),
        )

    class PongMidfieldOverlay(renpy.Displayable):
        def __init__(self, width, height, circle_ratio=0.26, **kwargs):
            super(PongMidfieldOverlay, self).__init__(**kwargs)
            self.width = int(width)
            self.height = int(height)
            self.circle_ratio = float(circle_ratio)

        def render(self, width, height, st, at):
            rv = ren_render.Render(self.width, self.height)
            surface = ren_pgrender.surface((self.width, self.height), True)
            surface = surface.convert_alpha()
            surface.fill((0, 0, 0, 0))

            dash_height = 36
            dash_gap = 18
            dash_width = 4
            dash_color = _color_to_rgba_tuple("#9db4d8aa")
            x_center = self.width / 2 - dash_width / 2
            for dash_y in range(-dash_height, self.height + dash_height, dash_height + dash_gap):
                pygame.draw.rect(surface, dash_color, pygame.Rect(x_center, dash_y, dash_width, dash_height))

            circle_radius = int(min(self.width, self.height) * self.circle_ratio)
            dash_count = 64
            dash_ratio = 0.55
            thickness = 6
            base = math.radians(90)
            center = (self.width / 2.0, self.height / 2.0)
            dash_span = 2 * math.pi / dash_count
            dash_length = dash_span * dash_ratio
            circle_color = _color_to_rgba_tuple("#7fb9ff")

            for i in range(dash_count):
                start = base + dash_span * i
                end = start + dash_length
                start_pos = (
                    center[0] + math.cos(start) * circle_radius,
                    center[1] + math.sin(start) * circle_radius,
                )
                end_pos = (
                    center[0] + math.cos(end) * circle_radius,
                    center[1] + math.sin(end) * circle_radius,
                )
                pygame.draw.line(surface, circle_color, start_pos, end_pos, thickness)

            inner_radius = max(12, circle_radius - 20)
            pygame.draw.circle(
                surface,
                _color_to_rgba_tuple("#070e1d"),
                (int(center[0]), int(center[1])),
                inner_radius,
                8,
            )

            rv.blit(surface, (0, 0))
            return rv

        def visit(self):
            return []

    def clamp(value, low, high):
        return max(low, min(high, value))

    def reset_pong_ball(serve_to="left"):
        global pong_ball_x, pong_ball_y, pong_ball_vx, pong_ball_vy, pong_message
        pong_ball_x = 0.5
        pong_ball_y = 0.5
        horizontal = random.uniform(0.35, 0.55)
        horizontal *= -1 if serve_to == "left" else 1
        pong_ball_vx = horizontal
        pong_ball_vy = random.uniform(-0.35, 0.35)
        pong_message = "Serving toward {} goal.".format("left" if horizontal < 0 else "right")

    def reset_pong_game():
        global pong_left_score, pong_right_score, pong_paddle_left_y, pong_paddle_right_y
        global pong_running, pong_message, pong_last_point, pong_paused, pong_last_winner, pong_mode
        global pong_right_manual_override, pong_left_velocity, pong_right_velocity
        pong_left_score = 0
        pong_right_score = 0
        pong_paddle_left_y = 0.5
        pong_paddle_right_y = 0.5
        pong_running = True
        pong_paused = False
        pong_last_point = None
        pong_last_winner = None
        pong_right_manual_override = False
        pong_left_velocity = 0.0
        pong_right_velocity = 0.0
        reset_pong_ball(serve_to="right")
        if pong_mode == "player_vs_ai":
            pong_message = "W/S to move. The AI controls the right paddle."
        else:
            pong_message = "W/S moves left paddle. Arrows move right paddle."

    def set_pong_mode(mode):
        global pong_mode
        if mode not in ("player_vs_ai", "player_vs_player"):
            return
        if pong_mode != mode:
            pong_mode = mode
            reset_pong_game()

    def move_paddle(side, direction, dt=PONG_DT):
        global pong_paddle_left_y, pong_paddle_right_y
        amount = direction * PONG_PADDLE_SPEED * dt
        if side == "left":
            pong_paddle_left_y = clamp(pong_paddle_left_y + amount, PONG_PADDLE_HEIGHT / 2, 1 - PONG_PADDLE_HEIGHT / 2)
        else:
            pong_paddle_right_y = clamp(pong_paddle_right_y + amount, PONG_PADDLE_HEIGHT / 2, 1 - PONG_PADDLE_HEIGHT / 2)

    def pong_toggle_pause():
        global pong_paused, pong_message
        pong_paused = not pong_paused
        pong_message = "Paused." if pong_paused else "Keep volleying!"

    def pong_point_scored(side):
        global pong_left_score, pong_right_score, pong_running, pong_message, pong_last_point, pong_last_winner
        if side == "left":
            pong_left_score += 1
        else:
            pong_right_score += 1
        pong_last_point = side
        pong_message = "{} team scores!".format("Left" if side == "left" else "Right")
        reset_pong_ball(serve_to="right" if side == "left" else "left")
        if pong_left_score >= pong_target_score:
            pong_running = False
            pong_last_winner = "Left"
            pong_message = "Left paddle claims victory!"
        elif pong_right_score >= pong_target_score:
            pong_running = False
            pong_last_winner = "Right"
            pong_message = "Right paddle claims victory!"

    def _approach_velocity(current, desired, accel, dt):
        if desired > current:
            current = min(desired, current + accel * dt)
        elif desired < current:
            current = max(desired, current - accel * dt)
        else:
            if current > 0:
                current = max(0.0, current - accel * dt)
            elif current < 0:
                current = min(0.0, current + accel * dt)
        if abs(current) < 1e-4:
            return 0.0
        return current

    def pong_player_step():
        global pong_right_manual_override, pong_left_velocity, pong_right_velocity, pong_mode
        if pong_paused or not pong_running:
            pong_right_manual_override = False
            pong_left_velocity = 0.0
            pong_right_velocity = 0.0
            return

        dt = PONG_DT
        pressed = pygame.key.get_pressed()

        left_desired = 0
        if pressed[pygame.K_w]:
            left_desired -= 1
        if pressed[pygame.K_s]:
            left_desired += 1
        pong_left_velocity = _approach_velocity(pong_left_velocity, left_desired, PONG_PADDLE_ACCEL, dt)
        if pong_left_velocity:
            move_paddle("left", pong_left_velocity, dt)

        if pong_mode == "player_vs_player":
            right_desired = 0
            if pressed[pygame.K_UP]:
                right_desired -= 1
            if pressed[pygame.K_DOWN]:
                right_desired += 1
            pong_right_velocity = _approach_velocity(pong_right_velocity, right_desired, PONG_PADDLE_ACCEL, dt)
            if pong_right_velocity:
                move_paddle("right", pong_right_velocity, dt)
            else:
                pong_right_velocity = 0.0
            pong_right_manual_override = False
        else:
            pong_right_velocity = _approach_velocity(pong_right_velocity, 0, PONG_PADDLE_ACCEL, dt)
            pong_right_manual_override = False

    def pong_ai_step():
        global pong_right_velocity, pong_mode
        if not pong_ai_enabled or pong_paused or not pong_running:
            return
        if pong_mode == "player_vs_player":
            return
        if pong_right_manual_override:
            return

        dt = PONG_DT
        delta = pong_ball_y - pong_paddle_right_y
        desired = clamp(delta * 8.0, -1.0, 1.0)
        pong_right_velocity = _approach_velocity(pong_right_velocity, desired, PONG_PADDLE_ACCEL, dt)
        if pong_right_velocity:
            move_paddle("right", pong_right_velocity, dt)

    def pong_ball_step():
        global pong_ball_x, pong_ball_y, pong_ball_vx, pong_ball_vy
        if not pong_running or pong_paused:
            return
        pong_ball_x += pong_ball_vx * PONG_DT
        pong_ball_y += pong_ball_vy * PONG_DT
        if pong_ball_y <= PONG_BALL_RADIUS:
            pong_ball_y = PONG_BALL_RADIUS
            pong_ball_vy = abs(pong_ball_vy)
        elif pong_ball_y >= 1 - PONG_BALL_RADIUS:
            pong_ball_y = 1 - PONG_BALL_RADIUS
            pong_ball_vy = -abs(pong_ball_vy)
        # Left paddle collision
        paddle_half = PONG_PADDLE_HEIGHT / 2
        paddle_left_edge = PONG_PADDLE_WIDTH
        paddle_right_edge = 1 - PONG_PADDLE_WIDTH
        if pong_ball_x - PONG_BALL_RADIUS <= paddle_left_edge:
            if abs(pong_ball_y - pong_paddle_left_y) <= paddle_half:
                pong_ball_x = paddle_left_edge + PONG_BALL_RADIUS
                pong_ball_vx = abs(pong_ball_vx)
                pong_ball_vy += (pong_ball_y - pong_paddle_left_y) * 0.6
        if pong_ball_x + PONG_BALL_RADIUS >= paddle_right_edge:
            if abs(pong_ball_y - pong_paddle_right_y) <= paddle_half:
                pong_ball_x = paddle_right_edge - PONG_BALL_RADIUS
                pong_ball_vx = -abs(pong_ball_vx)
                pong_ball_vy += (pong_ball_y - pong_paddle_right_y) * 0.6
        if pong_ball_x < 0:
            pong_point_scored("right")
        elif pong_ball_x > 1:
            pong_point_scored("left")

style pong_ball:
    xanchor 0.5
    yanchor 0.5
    background Solid("#f5f5f5")
    xsize 24
    ysize 24

style pong_paddle:
    background Solid("#f5b342")
    xsize 18
    ysize int(PONG_FIELD_HEIGHT * PONG_PADDLE_HEIGHT)

style pong_heading:
    size 44
    color "#f5f8ff"
    xalign 0.5

style pong_message:
    size 24
    color "#b2bed6"
    xalign 0.5

style pong_score:
    size 92
    color "#f6f7ff"
    xanchor 0.5
    yanchor 0.0
    outlines [(4, "#05070d7a", 0, 0)]

style pong_score_label:
    size 28
    color "#6fd8ff"
    xanchor 0.5
    yanchor 0.0

style pong_score_big:
    size 118
    color "#f6f7ff"
    xanchor 0.5
    yanchor 0.0
    outlines [(5, "#03060c88", 0, 0)]

style pong_label_blue:
    size 32
    color "#50c8ff"
    xanchor 0.5
    yanchor 0.0

style pong_label_red:
    size 32
    color "#ff8a87"
    xanchor 0.5
    yanchor 0.0

style pong_status:
    size 24
    color "#c3d2ef"
    xalign 0.5

screen pong_midfield_overlay(field_w, field_h, circle_ratio=0.26):
    # Uses the custom displayable so the dashed line + rings render on every renderer layer.
    add PongMidfieldOverlay(field_w, field_h, circle_ratio=circle_ratio) xpos 0 ypos 0

screen pong_minigame():
    modal True
    tag menu
    zorder 200

    add Solid("#000000c8")

    if pong_running and not pong_paused:
        timer pong_tick_delay repeat True action [Function(pong_player_step), Function(pong_ball_step), Function(pong_ai_step)]


    frame:
        xalign 0.5
        yalign 0.5
        padding (28, 28)
        background Solid("#050912")

        vbox:
            spacing 18
            xalign 0.5

            text "Arcane Pong" style "pong_heading"

            hbox:
                spacing 140
                xalign 0.5
                vbox:
                    spacing -8
                    text "[pong_left_score]" style "pong_score_big"
                    text "P1" style "pong_label_blue"
                vbox:
                    spacing -8
                    text "[pong_right_score]" style "pong_score_big"
                    text ("AI" if pong_mode == "player_vs_ai" else "P2") style "pong_label_red" color ("#ff8e86" if pong_mode == "player_vs_ai" else "#7aedc1")

            text pong_message style "pong_status"

            $ field_w = int(PONG_FIELD_WIDTH)
            $ field_h = int(PONG_FIELD_HEIGHT)
            $ paddle_h = int(PONG_FIELD_HEIGHT * PONG_PADDLE_HEIGHT)
            $ paddle_w = max(4, int(PONG_PADDLE_WIDTH * field_w))
            $ paddle_left_top = int(pong_paddle_left_y * field_h - paddle_h / 2)
            $ paddle_right_top = int(pong_paddle_right_y * field_h - paddle_h / 2)
            $ paddle_left_face = PONG_PADDLE_WIDTH * field_w
            $ paddle_right_face = (1 - PONG_PADDLE_WIDTH) * field_w
            $ paddle_left_x = int(paddle_left_face - paddle_w)
            $ paddle_right_x = int(paddle_right_face)
            $ ball_size = max(6, int(PONG_BALL_RADIUS * field_w * 2))
            $ ball_x = int(pong_ball_x * field_w - ball_size / 2)
            $ ball_y = int(pong_ball_y * field_h - ball_size / 2)

            fixed:
                xsize field_w
                ysize field_h
                add Solid("#080f1b") xysize (field_w, field_h)
                add Solid("#0f1624") xysize (field_w - 12, field_h - 12) xpos 6 ypos 6

                $ dash_height = 36
                $ dash_gap = 18
                $ dash_color = "#9db4d8aa"
                for dash_y in range(-dash_height, field_h + dash_height, dash_height + dash_gap):
                    add Solid(dash_color) xpos field_w / 2 - 2 ypos dash_y xysize (4, dash_height)

                $ circle_ratio = 0.26
                use pong_midfield_overlay(field_w=field_w, field_h=field_h, circle_ratio=circle_ratio)

                add Solid("#32afff") xysize (paddle_w, paddle_h) xpos paddle_left_x ypos paddle_left_top
                add Solid("#ff6d6d") xysize (paddle_w, paddle_h) xpos paddle_right_x ypos paddle_right_top

                add Solid("#1f2a3d") xysize (ball_size + 10, ball_size + 10) xpos ball_x - 5 ypos ball_y - 5
                add Solid("#f5f5f5") xysize (ball_size, ball_size) xpos ball_x ypos ball_y

            hbox:
                spacing 20
                xalign 0.5
                textbutton "Reset" action Function(reset_pong_game)
                textbutton "Pause" action Function(pong_toggle_pause)
                textbutton "Player vs AI" action Function(set_pong_mode, "player_vs_ai") selected (pong_mode == "player_vs_ai")
                textbutton "Player vs Player" action Function(set_pong_mode, "player_vs_player") selected (pong_mode == "player_vs_player")
                textbutton "Exit" action Return(False)

label pong_minigame:
    $ reset_pong_game()
    $ renpy.call_screen("pong_minigame")
    return
