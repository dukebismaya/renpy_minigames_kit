# Gameplay data model for dynamic character and quest tracking.
# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
init python:
    """Core gameplay data """

    QUEST_STATES = ("not_started", "in_progress", "completed")

    def _notify(message, category="info"):
        try:
            push_notification(message, category)
        except Exception:
            pass


    class CharacterData(object):
        """Stores arbitrary stats for a gameplay character."""

        def __init__(self, name, stats=None):
            self.name = name
            self.stats = stats.copy() if stats else {}

        def add_stat(self, stat, value):
            """Adds (or increments) a stat and returns the updated value."""
            current = self.stats.get(stat, 0)
            updated = current + value
            self.stats[stat] = updated
            return updated

        def get_stat(self, stat):
            return self.stats.get(stat, 0)


    class QuestData(object):
        """Quest tracker with status updates."""

        def __init__(self, title, description, status="not_started", requirements=None):
            if status not in QUEST_STATES:
                raise ValueError("Invalid quest status: {}".format(status))

            self.title = title
            self.description = description
            self.status = status
            self.requirements = list(requirements) if requirements else []

        def update_status(self, new_status):
            if new_status not in QUEST_STATES:
                raise ValueError("Invalid quest status: {}".format(new_status))

            self.status = new_status
            return self.status


    class GameState(object):
        """Manages the collections of characters and quests."""

        def __init__(self):
            self.characters = {}
            self.quests = {}
            self.tracked_quests = set()

        # Character helpers -------------------------------------------------
        def add_character(self, character):
            self.characters[character.name] = character
            _notify("New ally registered: {0}".format(character.name), "character")
            return character

        def get_character(self, name):
            return self.characters.get(name)

        def update_character_stat(self, name, stat, value):
            character = self.characters.get(name)
            if character is None:
                character = self.add_character(CharacterData(name))
            updated = character.add_stat(stat, value)
            _notify("{0} {1} {2:+} (-> {3})".format(name, stat.capitalize(), value, updated), "stat")
            return updated

        # Quest helpers -----------------------------------------------------
        def add_quest(self, quest, track=True):
            self.quests[quest.title] = quest
            if track:
                self.tracked_quests.add(quest.title)
            _notify("Quest added: {0}".format(quest.title), "quest")
            return quest

        def get_quest(self, title):
            return self.quests.get(title)

        def update_quest_status(self, title, new_status):
            quest = self.quests.get(title)
            if quest is None:
                raise KeyError("Quest '{}' does not exist".format(title))
            updated = quest.update_status(new_status)
            _notify("{0} status -> {1}".format(title, updated), "quest")
            return updated

        def is_tracked(self, title):
            return title in self.tracked_quests

        def set_quest_tracking(self, title, tracked=True):
            if tracked:
                self.tracked_quests.add(title)
                _notify("Tracking quest: {0}".format(title), "quest")
            else:
                self.tracked_quests.discard(title)
                _notify("Quest hidden: {0}".format(title), "quest")

        def quests_by_status(self, statuses=None, tracked_only=False):
            statuses = set(statuses) if statuses else None
            results = []
            for quest in self.quests.values():
                if statuses and quest.status not in statuses:
                    continue
                if tracked_only and quest.title not in self.tracked_quests:
                    continue
                results.append(quest)
            return results


    def build_initial_game_state():
        state = GameState()

        # Characters
        state.add_character(CharacterData(
            "Lady Seris",
            {
                "affection": 12,
                "trust": 8,
                "corruption": 2,
            },
        ))
        state.add_character(CharacterData(
            "Sir Galen",
            {
                "affection": 4,
                "trust": 11,
                "corruption": 5,
            },
        ))
        state.add_character(CharacterData(
            "Mistcaller Veya",
            {
                "affection": 6,
                "trust": 5,
                "corruption": 1,
            },
        ))
        state.add_character(CharacterData(
            "Archivist Bren",
            {
                "affection": 9,
                "trust": 14,
                "corruption": 0,
            },
        ))

        # Quests
        state.add_quest(QuestData(
            "Fortify the Watchtower",
            "Raise the rune shields before dusk falls on the valley.",
            status="in_progress",
            requirements=["Gather oak planks", "Inscribe ward sigils"],
        ), track=True)
        state.add_quest(QuestData(
            "Seal the Barrow Gate",
            "Keep the restless spirits from crossing into the keep.",
        ), track=True)
        state.add_quest(QuestData(
            "Map the Whispering Mire",
            "Chart safe routes through the fog-bound marsh for the envoy caravan.",
            requirements=["Secure lantern beacons", "Interview mire hermits"],
        ), track=False)
        state.add_quest(QuestData(
            "Decode the Argent Manuscript",
            "Bren seeks the cipher that unlocks the vault of relics.",
            status="not_started",
        ), track=False)

        return state


# Ensure a fresh state for each new game start.
default game_state = build_initial_game_state()