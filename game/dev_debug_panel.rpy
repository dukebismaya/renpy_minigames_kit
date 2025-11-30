# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.

default quest_tracker_enabled = True
default quest_tracker_filters = {
    "not_started": True,
    "in_progress": True,
    "completed": False,
}


init -2 python:
    if "dev_debug_listener" not in config.overlay_screens:
        config.overlay_screens.append("dev_debug_listener")

    if "quest_tracker_overlay" not in config.overlay_screens:
        config.overlay_screens.append("quest_tracker_overlay")


init python:
    import renpy.pygame as pygame
    from renpy.display.displayable import Displayable
    from renpy.display.pgrender import Surface
    from renpy.display.render import Render


    class DevDebugGrid(Displayable):
        """Small cached surface for the holographic tile background."""

        def __init__(self):
            super(DevDebugGrid, self).__init__()
            self.surface = Surface((64, 64), True)
            self._build()

        def _build(self):
            self.surface.fill((3, 8, 15, 232))
            pygame.draw.line(self.surface, (15, 248, 219, 120), (0, 63), (63, 63))
            pygame.draw.line(self.surface, (255, 82, 255, 120), (63, 0), (63, 63))

        def render(self, width, height, st, at):
            r = Render(64, 64)
            r.blit(self.surface, (0, 0))
            return r

    DEV_DEBUG_GRID = DevDebugGrid()


    def toggle_quest_tracker_filter(status):
        quest_tracker_filters[status] = not quest_tracker_filters.get(status, True)


    def toggle_quest_tracking(title):
        if not game_state:
            return
        game_state.set_quest_tracking(title, not game_state.is_tracked(title))


    def toggle_quest_tracker_visibility():
        global quest_tracker_enabled
        quest_tracker_enabled = not quest_tracker_enabled


transform dev_panel_pulse:
    alpha 0.95
    linear 1.6 alpha 0.85
    linear 1.6 alpha 0.95
    repeat


style dev_debug_frame is frame
style dev_debug_frame:
    background Solid("#050910E8")
    padding (30, 30)
    xalign 0.5
    yalign 0.5
    xmaximum 1000
    ymaximum 600

style dev_debug_column is frame
style dev_debug_column:
    background Solid("#071426B0")
    padding (20, 20)
    top_margin 10
    bottom_margin 10

style dev_debug_title is text
style dev_debug_title:
    font "gui/DejaVuSansMono.ttf"
    size 34
    color "#66f7ff"

style dev_debug_hint is text
style dev_debug_hint:
    font "gui/DejaVuSansMono.ttf"
    size 18
    color "#8cfbff"

style dev_debug_section is text
style dev_debug_section:
    font "gui/DejaVuSansMono.ttf"
    size 22
    color "#ff64da"

style dev_debug_text is text
style dev_debug_text:
    font "gui/DejaVuSansMono.ttf"
    size 18
    color "#a9d4ff"

style dev_debug_muted is text
style dev_debug_muted:
    font "gui/DejaVuSansMono.ttf"
    size 18
    color "#6b7a96"

style dev_debug_card_button is button
style dev_debug_card_button:
    background Solid("#0a1c31B8")
    hover_background Solid("#12305AF0")
    padding (14, 14)
    xfill True
    top_margin 10
    bottom_margin 10
    left_margin 5
    right_margin 5
    hover_sound ""

style dev_debug_card_button_text is dev_debug_text

style dev_debug_card_title is text
style dev_debug_card_title:
    font "gui/DejaVuSansMono.ttf"
    size 20
    color "#00f6ff"

style dev_debug_status is text
style dev_debug_status:
    font "gui/DejaVuSansMono.ttf"
    size 18
    color "#ff8ce6"

style quest_tracker_frame is frame
style quest_tracker_frame:
    background Solid("#071019E0")
    padding (12, 12)
    xalign 0.0
    yalign 0.0

style quest_tracker_title is text
style quest_tracker_title:
    font "gui/DejaVuSansMono.ttf"
    size 18
    color "#5cfdeb"

style quest_tracker_text is text
style quest_tracker_text:
    font "gui/DejaVuSansMono.ttf"
    size 16
    color "#b9d4ff"

style quest_manager_frame is frame
style quest_manager_frame:
    background Solid("#050910F2")
    padding (24, 24)
    xalign 0.5
    yalign 0.5
    xmaximum 900
    ymaximum 650

style quest_manager_heading is text
style quest_manager_heading:
    font "gui/DejaVuSansMono.ttf"
    size 28
    color "#66f7ff"

style quest_manager_text is text
style quest_manager_text:
    font "gui/DejaVuSansMono.ttf"
    size 18
    color "#b9d4ff"

style quest_manager_button is button
style quest_manager_button:
    background Solid("#0a1c31B8")
    hover_background Solid("#12305AF0")
    padding (10, 10)
    left_margin 5
    right_margin 5
    bottom_margin 5

style quest_manager_button_text is text
style quest_manager_button_text:
    font "gui/DejaVuSansMono.ttf"
    size 16
    color "#5cfdeb"


screen dev_debug_listener():
    key "shift_K_d" action ToggleScreen("dev_debug_panel")
    key "shift_K_q" action ToggleScreen("quest_tracker_manager")
    key "shift_K_t" action Function(toggle_quest_tracker_visibility)


screen dev_debug_panel():
    modal False
    zorder 200

    key "shift_K_d" action Hide("dev_debug_panel")
    key "game_menu" action Hide("dev_debug_panel")

    add LiveTile(DEV_DEBUG_GRID, size=(64, 64))
    add Solid("#070f1eAA") at dev_panel_pulse

    frame style "dev_debug_frame":
        vbox spacing 16:
            text "// DEV DEBUG PANEL" style "dev_debug_title"
            text "Shift+D to toggle   |   Data link: {color=#5cfdeb}ONLINE{/color}" style "dev_debug_hint"
            text "Shift+Q -> Quest manager" style "dev_debug_hint"
            text "Shift+T -> Quest HUD: {0}".format("ON" if quest_tracker_enabled else "OFF") style "dev_debug_hint"

            frame style "dev_debug_column":
                vbox spacing 8:
                    text "CHARACTER TELEMETRY" style "dev_debug_section"
                    if game_state and game_state.characters:
                        viewport:
                            draggable True
                            mousewheel True
                            scrollbars "vertical"
                            has vbox
                            for character in game_state.characters.values():
                                use dev_debug_character_card(character=character)
                    else:
                        text "-- No characters registered --" style "dev_debug_muted"


screen dev_debug_character_card(character):
    button style "dev_debug_card_button" action NullAction():
        vbox spacing 2:
            text character.name style "dev_debug_card_title"
            if character.stats:
                for stat, value in character.stats.items():
                    text "{0:<12}: {1}".format(stat.capitalize(), value) style "dev_debug_text"
            else:
                text "No stats logged" style "dev_debug_muted"


screen dev_debug_quest_card(quest):
    button style "dev_debug_card_button" action NullAction():
        vbox spacing 4:
            text quest.title style "dev_debug_card_title"
            text quest.description style "dev_debug_text"
            text quest.status.upper() style "dev_debug_status"
            if quest.requirements:
                text "Requirements:" style "dev_debug_text"
                for req in quest.requirements:
                    text "- {0}".format(req) style "dev_debug_text"
            else:
                text "No requirements" style "dev_debug_muted"


screen quest_tracker_overlay():
    zorder 50
    if quest_tracker_enabled and game_state and game_state.quests:
        $ allowed_statuses = [s for s, enabled in quest_tracker_filters.items() if enabled]
        if allowed_statuses:
            $ tracked_quests = [
                quest for quest in game_state.quests.values()
                if game_state.is_tracked(quest.title) and quest.status in allowed_statuses
            ]
        else:
            $ tracked_quests = []

        if tracked_quests:
            frame style "quest_tracker_frame":
                vbox spacing 6:
                    text "// QUEST TRACKER" style "quest_tracker_title"
                    for quest in tracked_quests:
                        vbox spacing 0:
                            text quest.title style "quest_tracker_text"
                            text "Status: {0}".format(quest.status) style "quest_tracker_text"
                            if quest.requirements:
                                text "Req: {0}".format(", ".join(quest.requirements)) style "quest_tracker_text"
                            else:
                                text "Req: --" style "quest_tracker_text"
        else:
            frame style "quest_tracker_frame":
                text "// No tracked quests" style "quest_tracker_text"


screen quest_tracker_manager():
    modal False
    zorder 205

    key "shift_K_q" action Hide("quest_tracker_manager")
    key "game_menu" action Hide("quest_tracker_manager")

    add Solid("#010409A0")

    frame style "quest_manager_frame":
        vbox spacing 18:
            text "// QUEST MANAGER" style "quest_manager_heading"
            text "Toggle visibility filters and tracking (Shift+Q)" style "quest_manager_text"
            textbutton "Quest HUD: {0}".format("ON" if quest_tracker_enabled else "OFF") style "quest_manager_button" text_style "quest_manager_button_text" action Function(toggle_quest_tracker_visibility)

            $ status_labels = [
                ("not_started", "Not Started"),
                ("in_progress", "In Progress"),
                ("completed", "Completed"),
            ]

            hbox spacing 12:
                for code, label in status_labels:
                    $ enabled = quest_tracker_filters.get(code, True)
                    textbutton "{0}: {1}".format(label, "ON" if enabled else "OFF") style "quest_manager_button" text_style "quest_manager_button_text" action Function(toggle_quest_tracker_filter, code)

            if not any(quest_tracker_filters.values()):
                text "No statuses selected. The HUD will hide all quests." style "quest_manager_text"

            if game_state and game_state.quests:
                viewport:
                    draggable True
                    mousewheel True
                    scrollbars "vertical"
                    has vbox spacing 10
                    for quest in game_state.quests.values():
                        $ tracked = game_state.is_tracked(quest.title)
                        frame style "dev_debug_column":
                            vbox spacing 4:
                                text "{0}".format(quest.title) style "dev_debug_card_title"
                                text "Status: {0}".format(quest.status) style "quest_manager_text"
                                text "Req: {0}".format(", ".join(quest.requirements) if quest.requirements else "--") style "quest_manager_text"
                                textbutton ("Tracking" if tracked else "Hidden") style "quest_manager_button" text_style "quest_manager_button_text" action Function(toggle_quest_tracking, quest.title)
            else:
                text "No quests registered." style "quest_manager_text"