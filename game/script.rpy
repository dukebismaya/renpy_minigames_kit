# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
define e = Character("Eileen")


transform splash_tag_reveal:
    alpha 0.0
    zoom 0.97
    on show:
        linear 0.6 alpha 1.0 zoom 1.0
    on hide:
        linear 0.4 alpha 0.0 zoom 1.03

transform splash_logo_reveal:
    alpha 0.0
    zoom 1.08
    on show:
        linear 0.9 alpha 1.0 zoom 1.0
    on hide:
        linear 0.4 alpha 0.0 zoom 1.1

transform splash_glow_pulse:
    alpha 0.0
    on show:
        linear 0.6 alpha 0.35
        linear 0.8 alpha 0.12
    on hide:
        linear 0.4 alpha 0.0

transform splash_glow_anchor:
    xalign 0.5
    yalign 0.5
    zoom 1.05

transform splash_tag_anchor:
    xalign 0.5
    yalign 0.32

transform splash_logo_anchor:
    xalign 0.5
    yalign 0.52


label splashscreen:
    # $ _preferences.fullscreen = True
    $ notifications_enabled = False
    scene black with Pause(0.25)
    pause 0.1
    play sound "audio/logo_reveal.mp3"

    show expression Solid("#ff6d3a1e") as splash_glow at splash_glow_anchor, splash_glow_pulse
    show expression Text("POWERED BY", size=48, color=gui.accent_color, outlines=[(3, "#120400", 0, 0)], kerning=3) as splash_tag at splash_tag_anchor, splash_tag_reveal
    pause 0.4
    show expression Text("REN'PY", size=138, color="#ffb347", outlines=[(8, "#2b0a00", 0, 0)]) as splash_logo at splash_logo_anchor, splash_logo_reveal

    pause 2.4

    hide splash_logo with Dissolve(0.45)
    hide splash_tag with Dissolve(0.4)
    hide splash_glow with Dissolve(0.6)

    stop sound fadeout 0.6

    return


label start:
    $ quick_menu = False
    $ toggle_quest_tracker_visibility()
    scene black with fade
    play music "audio/intro_music.mp3" fadein 1.5
    show text "Developed by Knox Emberlyn" at truecenter with dissolve
    pause 1.8
    hide text with dissolve

    # stop music fadeout 1.0
    # $ quick_menu = True
    # $ toggle_quest_tracker_visibility()
    $ notifications_enabled = True
    # play music "audio/a-robust-crew.mp3" fadein 1.5

    scene cg1

    e "Welcome to Caer Entropy. Before the dignitaries arrive, we capture this overview of the fortress shimmering with fresh wards."

    scene cg2

    e "Here in the war room we brief investors—notice how the runic scryer mirrors any stat or quest they request."

    # scene bg room
    # show eileen happy

    e "Shift+D brings the telemetry overlay to life, while Shift+Q opens the quest ledger."

    e "Our GameState chronicles the keep's champions and vows. Let's stress it like a proper royal demonstration."

    menu:
        "Rally Lady Seris atop the watchtower":
            scene cg3:
                xsize 1920 ysize 1080
            e "Seris grips the banner and rallies the scouts. Loyalty swells along the wall."
            $ game_state.update_character_stat("Lady Seris", "trust", 3)
            $ game_state.update_quest_status("Fortify the Watchtower", "completed")
            e "The rune-shields hum to life; the crowd sees the quest flip to completed without further script edits."

        "Let Sir Galen test the barrow wards":
            scene cg4:
                xsize 1920 ysize 1080
            e "Galen draws on forbidden sigils—effective, if a touch unsettling."
            $ game_state.update_character_stat("Sir Galen", "corruption", 2)
            $ game_state.update_quest_status("Seal the Barrow Gate", "in_progress")
            e "The gate groans but holds, and you can watch its status move to in-progress on the tracker."

        "Start the mini-game showcase":
            jump demo_minigames

    e "Now let's highlight some of the new faces stored inside the data model."

    menu:
        "Consult Mistcaller Veya about the Whispering Mire routes":
            scene cg5:
                xsize 1920 ysize 1080
            e "Veya sketches safe passages through the mire with drifting will-o'-wisps."
            $ game_state.update_character_stat("Mistcaller Veya", "trust", 2)
            $ game_state.update_quest_status("Map the Whispering Mire", "in_progress")
            $ game_state.set_quest_tracking("Map the Whispering Mire", True)
            e "Watch the quest pop onto the HUD as soon as we flip tracking on."

        "Help Archivist Bren decode the Argent Manuscript":
            scene cg6:
                xsize 1920 ysize 1080
            e "Bren coaxes hidden sigils from the Argent Manuscript; the vault wards shiver."
            $ game_state.update_character_stat("Archivist Bren", "trust", 1)
            $ game_state.update_quest_status("Decode the Argent Manuscript", "in_progress")
            $ game_state.set_quest_tracking("Decode the Argent Manuscript", True)
            e "Since that vow was untracked before, the quest tracker immediately adds it now."

    e "Every choice mutates the data model, and the debug utilities echo those shifts instantly. Add more heroes or vows and the system scales without rewiring labels."

    e "If you want to prove that new data can be provisioned live, try one of these sandbox actions."

    menu:
        "Recruit Archer Lys on the fly":
            scene cg7:
                xsize 1920 ysize 1080
            $ lys_exists = game_state.get_character("Archer Lys")
            if not lys_exists:
                $ lys_card = CharacterData("Archer Lys", {"affection": 7, "trust": 6, "corruption": 0})
                $ game_state.add_character(lys_card)
                e "Archer Lys arrives with a fresh telemetry card generated entirely from this choice."
            else:
                e "Lys is already logged, so we just ping her stats panel."

            if not game_state.get_quest("Secure the Skybridge"):
                $ skybridge = QuestData(
                    "Secure the Skybridge",
                    "Clear the rope bridges of raiders so merchants can cross.",
                    status="in_progress",
                    requirements=["Sweep eastern parapet", "Reset warding beacons"],
                )
                $ game_state.add_quest(skybridge, track=True)
                e "The quest HUD instantly lists 'Secure the Skybridge' because we tracked it when adding."
            else:
                e "That quest already exists—feel free to toggle it via Shift+Q if needed."

        "Author a brand-new vow for the envoy":
            scene cg8:
                xsize 1920 ysize 1080
            $ vow_name = "Escort the Moon Envoy"
            if not game_state.get_quest(vow_name):
                $ envoy_quest = QuestData(
                    vow_name,
                    "Guarantee the moon envoy reaches the chapel with her starlit cargo.",
                    status="not_started",
                    requirements=["Brief honor guard", "Sanctify procession route"],
                )
                $ game_state.add_quest(envoy_quest, track=False)
                e "We spawned a vow without auto-tracking it. Open Shift+Q to toggle it when the team is ready."
            else:
                e "The moon envoy vow already sits in the database—we won't duplicate it."

            if not game_state.get_character("Shield-Bearer Otmar"):
                $ otmar = CharacterData("Shield-Bearer Otmar", {"affection": 5, "trust": 9, "corruption": 1})
                $ game_state.add_character(otmar)
                e "Otmar joins the roster to guard the envoy, giving the overlay another stat card without touching core scripts."
            else:
                e "Otmar's already guarding the envoy, so no duplicate entry is created."

    e "Before we adjourn, want to sanity check the rune-matrix that powers our candy-crush diversion, the serpent run in the training yard, the sigil grid trials, or the arcane pong table?"

    menu demo_minigames:
        "Launch the sigil-matching mini-game":
            call match_minigame
            if match_goal_met():
                e "Nicely done. The telemetry flags the board as stable once you clear enough sigils."
            else:
                e "Even without the victory threshold, the board proves the systems are humming."

        "Run the snake mini-game":
            call snake_minigame
            e "Serpent drills complete. The cadets love watching that pathfinding in action."

        "Play the tic-tac-toe sigil grid":
            call tic_tac_toe_minigame
            e "Simple, but it convinces the nobles that our AI can duel on even the smallest grid."
        
        "Test tic-tac-toe":
            call tic_tac_toe_line_test
            e ""

        "Preview the circle displayable":
            call show_circle_demo
            e "Custom renderables like that circle can be slotted into any HUD or screen with just one line."

        "Challenge the arcane pong table":
            call pong_minigame
            e "Impressive volleys. The rune-ball tracking shows off our physics layer beautifully."

        "Skip the diversions for now":
            e "Very well—we can revisit the sigil arrays, serpent drills, grid trials, and pong table whenever the pitch needs more sparkle."

    return
