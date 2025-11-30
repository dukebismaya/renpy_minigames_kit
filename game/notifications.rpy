# Notification helpers using Ren'Py's built-in popup.
# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.

default notifications_enabled = False

init -10 python:
    CATEGORY_PREFIX = {
        "stat": "Stat",
        "quest": "Quest",
        "character": "Ally",
        "info": "Info",
    }

    def push_notification(message, category="info"):
        if not renpy.store.notifications_enabled:
            return
        prefix = CATEGORY_PREFIX.get(category, "Info")
        try:
            renpy.notify("[{0}] {1}".format(prefix, message))
        except Exception:
            pass
