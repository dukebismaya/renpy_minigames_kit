init python:
    import os
    import copy
    import renpy.exports as renpy
    import renpy.loader as ren_loader
    import renpy.pygame as pygame

    from renpy import config as ren_config
    from renpy.display.core import Displayable
    from renpy.display.render import Render
    from renpy.store import Solid, Image

    _SHIP_PREVIEW_MAX_WIDTH = 300.0
    _SHIP_ROSTER_MAX_WIDTH = 70.0
    _SHIP_RUNTIME_MAX_WIDTH = 150.0
    _WAVE_LIMIT_MIN = 5
    _WAVE_LIMIT_MAX = 50
    _WAVE_LIMIT_STEP = 5

    _SPACE_REBELLION_SHIPS = [
        {
            "id": "astra",
            "name": "Astra Scout",
            "role": "Interceptor",
            "sprite": "sprites/ships/ship1.png",
            "preview": "minigames/spacerebellion/assets/sprites/ships/ship1.png",
            "speed": 460,
            "acceleration": 1500,
            "health": 85,
            "cooldown": 0.16,
            "damage": 0.9,
            "difficulty": "Easy",
            "traits": ["Evasive Thrusters", "Volley 0.16s"],
            "description": "Lightning-fast recon craft built for dodging curtains of plasma.",
            "color": "#7cf5d4",
        },
        {
            "id": "vanguard",
            "name": "Vanguard Mk II",
            "role": "Balanced Fighter",
            "sprite": "sprites/ships/ship4.png",
            "preview": "minigames/spacerebellion/assets/sprites/ships/ship4.png",
            "speed": 400,
            "acceleration": 1300,
            "health": 110,
            "cooldown": 0.18,
            "damage": 1.0,
            "difficulty": "Normal",
            "traits": ["Adaptive Shielding", "Balanced Arsenal"],
            "description": "Reliable strike craft that balances speed, armor, and weapon cadence.",
            "color": "#9ec8ff",
        },
        {
            "id": "nova",
            "name": "Nova Reaver",
            "role": "Gunship",
            "sprite": "sprites/ships/ship7.png",
            "preview": "minigames/spacerebellion/assets/sprites/ships/ship7.png",
            "speed": 340,
            "acceleration": 1100,
            "health": 140,
            "cooldown": 0.21,
            "damage": 1.4,
            "difficulty": "Hard",
            "traits": ["Siege Cannons", "Reinforced Hull"],
            "description": "Heavy gunship that shrugs off volleys and punishes bosses with brutal shots.",
            "color": "#ffb08d",
        },
        {
            "id": "aurora",
            "name": "Aurora Lance",
            "role": "Experimental",
            "sprite": "sprites/ships/Ship_1_D_Small.png",
            "preview": "minigames/spacerebellion/assets/sprites/ships/Ship_1_D_Small.png",
            "speed": 420,
            "acceleration": 1400,
            "health": 95,
            "cooldown": 0.14,
            "damage": 1.15,
            "difficulty": "Expert",
            "traits": ["Beam-Ready", "Precision Spread"],
            "description": "Prototype lance frigate with experimental capacitors and razor spread shots.",
            "color": "#ffd38f",
        },
    ]


    def space_rebellion_ship_catalog():
        catalog = [copy.deepcopy(ship) for ship in _SPACE_REBELLION_SHIPS]
        for ship in catalog:
            _space_rebellion_prepare_ship_entry(ship)
        return catalog


    def space_rebellion_default_ship():
        catalog = space_rebellion_ship_catalog()
        return catalog[0] if catalog else None


    def _space_rebellion_prepare_ship_entry(ship):
        ship.setdefault("max_runtime_width", _SHIP_RUNTIME_MAX_WIDTH)
        preview_path = ship.get("preview")
        width, _ = _space_rebellion_image_size(preview_path)
        ship["_preview_zoom"] = _space_rebellion_zoom_for_width(width, _SHIP_PREVIEW_MAX_WIDTH)
        ship["_roster_zoom"] = _space_rebellion_zoom_for_width(width, _SHIP_ROSTER_MAX_WIDTH)


    def _space_rebellion_image_size(path):
        if not path:
            return (0, 0)
        try:
            resolved = ren_loader.transfn(path)
            if not os.path.exists(resolved):
                return (0, 0)
            image = pygame.image.load(resolved)
            if image:
                return image.get_size()
        except Exception:
            return (0, 0)
        return (0, 0)


    def _space_rebellion_zoom_for_width(width, target):
        if width <= 0 or target <= 0:
            return 1.0
        if width <= target:
            return 1.0
        return float(target) / float(width)


    class SpaceRebellionDisplayable(Displayable):
        """Custom displayable that feeds the pygame-driven engine each frame."""

        @staticmethod
        def _serialize_ship_profile(profile):
            if not profile:
                return None
            serialized = dict(profile)
            serialized.pop("_sprite_surface", None)
            return serialized

        def __init__(self, width=960, height=600, seed=None, ship_profile=None, wave_limit=None, **kwargs):
            super(SpaceRebellionDisplayable, self).__init__(**kwargs)
            self.width = int(width)
            self.height = int(height)
            self.focusable = True
            asset_root = _space_rebellion_asset_root()
            self.engine = SpaceRebellionEngine(asset_root=asset_root, width=self.width, height=self.height, seed=seed)
            self._input_state = {"left": False, "right": False, "up": False, "down": False}
            self._last_st = None
            self.ship_profile = ship_profile or space_rebellion_default_ship()
            self.wave_limit = None
            if self.ship_profile:
                self.engine.set_ship_profile(self.ship_profile)
            self.set_wave_limit(wave_limit)

        def __getstate__(self):
            return {
                "width": self.width,
                "height": self.height,
                "ship_profile": self._serialize_ship_profile(self.ship_profile),
                "wave_limit": self.wave_limit,
            }

        def __setstate__(self, state):
            self.__init__(
                width=state.get("width", 960),
                height=state.get("height", 600),
                ship_profile=state.get("ship_profile"),
                wave_limit=state.get("wave_limit"),
            )

        def reset(self):
            self.engine.reset()
            if self.ship_profile:
                self.engine.set_ship_profile(self.ship_profile)
            self._last_st = None
            for key in self._input_state:
                self._input_state[key] = False
            self.engine.set_direction(0, 0)
            self.engine.set_keyboard_fire(False)
            self.engine.set_mouse_fire(False)
            self.set_wave_limit(self.wave_limit)

        def set_ship_profile(self, profile):
            if profile is None:
                return
            self.ship_profile = profile
            self.engine.set_ship_profile(profile)

        def set_wave_limit(self, wave_limit):
            if wave_limit is None:
                self.wave_limit = None
            else:
                try:
                    wave_limit = int(wave_limit)
                except (TypeError, ValueError):
                    wave_limit = None
                else:
                    wave_limit = max(1, wave_limit)
                self.wave_limit = wave_limit
            self.engine.set_wave_limit(self.wave_limit)

        def render(self, width, height, st, at):
            if self._last_st is None:
                dt = 0.0
            else:
                dt = st - self._last_st
            self._last_st = st
            self.engine.update(dt)
            frame = self.engine.render()
            rv = Render(self.width, self.height)
            rv.blit(frame, (0, 0))
            renpy.redraw(self, 0)
            return rv

        def event(self, ev, x, y, st):
            handled = False
            if ev.type in (pygame.KEYDOWN, pygame.KEYUP):
                handled = self._handle_key_event(ev)
            elif ev.type == pygame.MOUSEMOTION:
                local_x = ev.pos[0] - x
                local_y = ev.pos[1] - y
                self.engine.set_pointer((local_x, local_y), use_mouse=True)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.engine.set_pointer((ev.pos[0] - x, ev.pos[1] - y), use_mouse=True)
                self.engine.set_mouse_fire(True)
                handled = True
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.engine.set_mouse_fire(False)
                handled = True
            # Prevent unhandled events from bubbling up and closing the screen.
            return None

        def _handle_key_event(self, ev):
            pressed = ev.type == pygame.KEYDOWN
            if ev.key in (pygame.K_a, pygame.K_LEFT):
                self._input_state["left"] = pressed
            elif ev.key in (pygame.K_d, pygame.K_RIGHT):
                self._input_state["right"] = pressed
            elif ev.key in (pygame.K_w, pygame.K_UP):
                self._input_state["up"] = pressed
            elif ev.key in (pygame.K_s, pygame.K_DOWN):
                self._input_state["down"] = pressed
            elif ev.key == pygame.K_SPACE:
                self.engine.set_keyboard_fire(pressed)
                return True
            else:
                return False
            dx = float(self._input_state["right"]) - float(self._input_state["left"])
            dy = float(self._input_state["down"]) - float(self._input_state["up"])
            self.engine.set_direction(dx, dy)
            return True


    def _space_rebellion_asset_root():
        relative = "minigames/spacerebellion/assets"
        try:
            return ren_loader.transfn(relative)
        except Exception:
            return os.path.join(ren_config.gamedir, relative)


    def _space_rebellion_finish(displayable, aborted):
        result = displayable.engine.result(aborted=aborted)
        print("Space Rebellion finish called:", aborted)
        renpy.return_statement(result)


default persistent.space_rebellion_ship_id = None
default persistent.space_rebellion_wave_limit = None


screen space_rebellion_ship_select():
    modal True
    tag menu
    default ships = space_rebellion_ship_catalog()
    default selected_id = persistent.space_rebellion_ship_id if hasattr(persistent, "space_rebellion_ship_id") else None
    default wave_limit = persistent.space_rebellion_wave_limit if hasattr(persistent, "space_rebellion_wave_limit") else None
    if ships and selected_id is None:
        $ selected_id = ships[0]["id"]
    $ selected_ship = None
    if ships:
        $ ship_ids = [ship["id"] for ship in ships]
        if selected_id not in ship_ids:
            $ selected_id = ship_ids[0]
        $ selected_index = ship_ids.index(selected_id)
        $ selected_ship = ships[selected_index]
    else:
        $ ship_ids = []
        $ selected_index = 0

    $ deploy_action = None
    if selected_ship:
        $ ship_payload = copy.deepcopy(selected_ship)
        $ ship_payload["wave_limit"] = wave_limit
        $ deploy_action = [
            SetField(persistent, "space_rebellion_ship_id", selected_ship["id"]),
            SetField(persistent, "space_rebellion_wave_limit", wave_limit),
            Return(ship_payload),
        ]

    add Solid("#00050ce6")

    frame:
        xalign 0.5
        yalign 0.5
        xmaximum 1180
        ymaximum 860
        padding (28, 28)
        background Solid("#050912f0")

        fixed:
            xfill True
            yfill True

            viewport:
                xfill True
                ymaximum 760
                scrollbars "vertical"
                mousewheel True
                draggable True
                pagekeys True
                vbox:
                    spacing 22

                    hbox:
                        xfill True
                        spacing 12
                        text "Select Your Starfighter" size 54
                        if selected_ship:
                            null width 0 xfill True
                            frame:
                                background Solid("#10233f")
                                padding (8, 6)
                                yalign 0.5
                                text selected_ship["difficulty"] size 24 color "#8bf3ff"

                    if selected_ship:
                        hbox:
                            spacing 28
                            xfill True
                            vbox:
                                spacing 12
                                frame:
                                    background Solid("#0c1628")
                                    padding (22, 20)
                                    xfill True
                                    vbox:
                                        spacing 12
                                        hbox:
                                            spacing 10
                                            text selected_ship["name"] size 36 color selected_ship.get("color", "#ffffff")
                                            text u"· {0}".format(selected_ship["role"]) size 24 color "#cdd5e5" ypos 4
                                        text selected_ship["description"] size 22 color "#b8c3d9"
                                        $ stat_rows = [
                                            ("Speed", selected_ship["speed"], 600),
                                            ("Hull", selected_ship["health"], 250),
                                            ("Fire Rate", int(1000 - selected_ship["cooldown"] * 1000), 1000),
                                            ("Damage", int(selected_ship["damage"] * 200), 300),
                                        ]
                                        frame:
                                            background Solid("#101c32")
                                            padding (16, 14)
                                            vbox:
                                                spacing 12
                                                grid 2 2:
                                                    spacing 18
                                                    for label, value, rng in stat_rows:
                                                        vbox:
                                                            spacing 4
                                                            text label size 20
                                                            bar value value range rng xmaximum 190
                                                if selected_ship.get("traits"):
                                                    vbox:
                                                        spacing 4
                                                        text "Traits" size 22 color "#8bf3ff"
                                                        for trait in selected_ship.get("traits", []):
                                                            text u"• {0}".format(trait) size 20 color "#f5fbff"
                                text "Use the arrow keys or scroll to browse. Pick a mission length below, then press Enter to deploy." size 20 color "#8aa3c7"
                            null width 0

                    $ wave_limit_label = "Endless" if wave_limit is None else "{} Waves".format(wave_limit)
                    $ wave_limit_value = wave_limit if wave_limit is not None else _WAVE_LIMIT_MIN
                    frame:
                        background Solid("#071021")
                        padding (18, 18)
                        vbox:
                            spacing 10
                            text "Mission Length" size 34 color "#9ec8ff"
                            text "Choose how many waves you want to clear before extraction." size 20 color "#b8c3d9"
                            hbox:
                                spacing 10
                                textbutton "∞" action SetScreenVariable("wave_limit", None) selected (wave_limit is None)
                                textbutton "-" action SetScreenVariable("wave_limit", max(_WAVE_LIMIT_MIN, wave_limit_value - _WAVE_LIMIT_STEP)) sensitive wave_limit is not None and wave_limit > _WAVE_LIMIT_MIN
                                frame:
                                    background Solid("#0c1628")
                                    padding (10, 6)
                                    xminimum 150
                                    xmaximum 200
                                    text wave_limit_label size 26 color "#f5fbff" xalign 0.5
                                textbutton "+" action SetScreenVariable("wave_limit", min(_WAVE_LIMIT_MAX, wave_limit + _WAVE_LIMIT_STEP if wave_limit is not None else _WAVE_LIMIT_MIN))
                            hbox:
                                spacing 8
                                for preset in (5, 10, 15, 20, 30):
                                    textbutton "{}".format(preset) action SetScreenVariable("wave_limit", preset) selected wave_limit == preset

                    text "Hangar Roster" size 34 color "#9ec8ff"
                    frame:
                        background Solid("#071021")
                        padding (18, 18)
                        viewport:
                            xsize 1120
                            ysize 460
                            scrollbars "vertical"
                            draggable True
                            mousewheel True
                            pagekeys True
                            vpgrid:
                                cols 3
                                spacing 20
                                for ship in ships:
                                    $ is_selected = ship["id"] == selected_id
                                    button:
                                        xsize 340
                                        ysize 210
                                        background Solid("#0b1424" if not is_selected else "#12304a")
                                        hover_background Solid("#1b2f4a")
                                        padding (14, 14)
                                        action SetScreenVariable("selected_id", ship["id"])
                                        has vbox
                                        spacing 8
                                        text ship["name"] size 26 color ship.get("color", "#ffffff")
                                        hbox:
                                            spacing 6
                                            text ship["role"] size 20 color "#cdd5e5"
                                            frame:
                                                background Solid("#0f223c")
                                                padding (4, 2)
                                                text ship["difficulty"] size 18 color "#9bd3ff"
                                        $ roster_zoom = ship.get("_roster_zoom", 1.0)
                                        add Transform(Image(ship["preview"]), zoom=roster_zoom) xalign 0.5
                                        text "Speed {0}".format(ship["speed"]) size 16 color "#8aa3c7"

            if selected_ship:
                frame:
                    anchor (1.0, 0.0)
                    xpos 0.97
                    ypos 0.02
                    xmaximum 360
                    background Solid("#040b16e6")
                    padding (16, 16)
                    at Transform(alpha=0.95)
                    vbox:
                        spacing 10
                        text "Ship Preview" size 20 color "#8bf3ff" xalign 0.5
                        $ preview = selected_ship["preview"]
                        $ preview_zoom = selected_ship.get("_preview_zoom", 1.0)
                        add Transform(Image(preview), zoom=preview_zoom, anchor=(0.5, 0.5)) xalign 0.5 yalign 0.5
                        text selected_ship["name"] size 24 color selected_ship.get("color", "#ffffff") xalign 0.5
                        text selected_ship["role"] size 20 color "#cdd5e5" xalign 0.5
                        text selected_ship["difficulty"] size 22 color "#8bf3ff" xalign 0.5

            hbox:
                spacing 20
                xalign 0.5
                yalign 1.0
                yoffset 20
                textbutton "Cancel" action Return(None)
                if deploy_action:
                    textbutton "Deploy" action deploy_action

    key "K_ESCAPE" action Return(None)
    if deploy_action:
        key "K_RETURN" action deploy_action
        key "K_KP_ENTER" action deploy_action
    if ship_ids:
        key "K_LEFT" action SetScreenVariable("selected_id", ship_ids[(selected_index - 1) % len(ship_ids)])
        key "K_RIGHT" action SetScreenVariable("selected_id", ship_ids[(selected_index + 1) % len(ship_ids)])


screen space_rebellion_minigame(displayable=None):
    modal True
    tag menu
    zorder 200
    default stats = {"score": 0, "wave": 0, "health": 0, "max_health": 0,
        "double_shot": 0.0, "rapid_fire": 0.0, "shield": 0.0,
        "game_over": False, "mission_complete": False, "wave_banner": 0.0,
        "boss_active": False, "ship_name": "Vanguard", "ship_role": "Fighter",
        "wave_limit": None}

    if displayable is None:
        $ displayable = SpaceRebellionDisplayable()
        $ displayable.reset()

    # Refresh stats without interrupting other interactions.
    timer 0.05 repeat True action SetScreenVariable("stats", displayable.engine.snapshot())

    key "K_ESCAPE" action Function(_space_rebellion_finish, displayable, True)
    key "dismiss" action NullAction()
    key "K_RETURN" action NullAction()
    key "K_SPACE" action NullAction()
    # Uncomment the following lines to not let Ren'Py steals WASD/arrow keys during minigame.
    for _intercept_key in ("K_a", "K_d", "K_w", "K_s", "K_LEFT", "K_RIGHT", "K_UP", "K_DOWN"):
        key _intercept_key action NullAction()

    add Solid("#00050cdd")

    frame:
        xalign 0.5
        yalign 0.5
        padding (28, 28)
        background Solid("#050912")

        vbox:
            spacing 18
            xalign 0.5

            text "Space Rebellion" size 54
            text "Hold Space or Left Mouse Button to fire." size 24 color "#9ec8ff"

            fixed:
                xsize displayable.width
                ysize displayable.height
                add displayable xpos 0 ypos 0
                if stats["wave_banner"] > 0 and not stats["game_over"]:
                    $ banner_alpha = min(1.0, stats["wave_banner"] / 2.2)
                    $ banner_text = "Wave {}".format(stats["wave"]) if stats["wave"] else "Ready"
                    if stats["boss_active"]:
                        $ banner_text = "Boss Incoming"
                    frame:
                        xalign 0.5
                        yalign 0.5
                        padding (36, 18)
                        background Solid("#0c1f3ed0")
                        at Transform(alpha=banner_alpha)
                        text banner_text size 48 color "#ffffff"
                if stats.get("mission_complete"):
                    frame:
                        xalign 0.5
                        yalign 0.5
                        padding (48, 32)
                        background Solid("#050912e6")
                        vbox:
                            spacing 16
                            text "Mission Complete" size 52 color "#9cf2ff"
                            text "Press Collect Rewards to extract." size 28 color "#dbe3ff"
                elif stats["game_over"]:
                    frame:
                        xalign 0.5
                        yalign 0.5
                        padding (48, 32)
                        background Solid("#050912e6")
                        vbox:
                            spacing 16
                            text "Mission Failed" size 52 color "#ffc8c2"
                            text "Press Collect Debrief to exit." size 28 color "#dbe3ff"

            $ wave_label = "Wave {}".format(stats["wave"]) if stats["wave"] else "Deployment"

            hbox:
                spacing 40
                xalign 0.5
                text "Score: {0:,}".format(stats["score"]) size 32
                text wave_label size 32
                text "Health: {}/{}".format(stats["health"], stats["max_health"]) size 32
                text "Ship: {}".format(stats["ship_name"]) size 32 color "#9ec8ff"
                $ limit_label = "Endless" if stats.get("wave_limit") in (None, 0) else "{} Waves".format(stats.get("wave_limit"))
                text "Target: {}".format(limit_label) size 32 color "#8bf3ff"
                if stats["rapid_fire"] > 0:
                    text "Rapid Fire {:.1f}s".format(stats["rapid_fire"]) size 32 color "#ffe07a"
                if stats["double_shot"] > 0:
                    text "Spread Shot {:.1f}s".format(stats["double_shot"]) size 32 color "#ffbcf5"
                if stats["shield"] > 0:
                    text "Shield {:.1f}s".format(stats["shield"]) size 32 color "#7cf5d4"
                if stats["boss_active"]:
                    text "Boss Active" size 32 color "#ff8d8d"

            if stats.get("mission_complete"):
                text "Mission complete! You cleared {0} waves and can extract whenever you're ready.".format(max(1, stats["wave"])) size 26 color "#9cf2ff"
            elif stats["game_over"]:
                text "Mission failed. Collect your debrief to exit." size 26 color "#ffaba5"
            else:
                $ mission_goal = "endless waves" if stats.get("wave_limit") in (None, 0) else "up to {0} waves".format(stats["wave_limit"])
                text "Move with WASD or arrows. Clear {0}, grab power-ups, and defeat every fifth-wave boss.".format(mission_goal) size 26 color "#9fc6ff"

            hbox:
                spacing 20
                xalign 0.5
                if not stats.get("mission_complete"):
                    textbutton "Abort Mission" action Function(_space_rebellion_finish, displayable, True)
                if stats.get("mission_complete"):
                    textbutton "Collect Rewards" action Function(_space_rebellion_finish, displayable, False)
                    textbutton "Run Again" action Function(displayable.reset)
                elif stats["game_over"]:
                    textbutton "Collect Debrief" action Function(_space_rebellion_finish, displayable, False)
                else:
                    textbutton "Restart" action Function(displayable.reset)


label space_rebellion_minigame:
    $ renpy.pause(0.0, hard=True)
    $ ship_profile = renpy.call_screen("space_rebellion_ship_select")
    if not ship_profile or not isinstance(ship_profile, dict):
        return None
    python:
        wave_limit = ship_profile.get("wave_limit")
        displayable = SpaceRebellionDisplayable(ship_profile=ship_profile, wave_limit=wave_limit)
        displayable.reset()
    $ result = renpy.call_screen("space_rebellion_minigame", displayable=displayable)
    $ print("Space Rebellion minigame result:", result)
    return result
