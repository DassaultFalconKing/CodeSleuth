from __future__ import annotations

from typing import Any


async def wait_for_screen_transition(pilot: Any) -> None:
    """Drain the Textual message pump through a modal screen-stack change.

    ``Pilot.click`` already ends with ``pause()``, which waits only for messages
    queued at the start of that wait. A ``Button.Pressed`` posted during that
    drain can still be in-flight, so the next assertion can observe the modal still
    active. ``wait_for_scheduled_animations`` is the documented Pilot API that
    performs another screen wait plus idle.
    """
    await pilot.wait_for_scheduled_animations()
