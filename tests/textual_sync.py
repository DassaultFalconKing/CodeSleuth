from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any


async def wait_for_screen_transition(
    pilot: Any,
    *,
    until: Callable[[], bool] | None = None,
    timeout: float = 2.0,
) -> None:
    """Drain Textual's message pump through a modal screen-stack change.

    ``Pilot.click`` ends with ``pause()``, but a ``Button.Pressed`` posted during
    that drain can still be in-flight. One additional animation drain is therefore
    not a reliable transition boundary on slower event loops.

    Without an explicit condition, perform two additional documented Pilot drains:
    one for the in-flight input message and one for work scheduled by its handler.
    Callers that need a specific screen state may provide ``until``; in that mode
    we keep yielding through the Pilot API until the condition is true or the
    bounded timeout expires. No wall-clock sleep is used as a synchronization
    oracle.
    """
    if until is None:
        await pilot.wait_for_scheduled_animations()
        await pilot.wait_for_scheduled_animations()
        return

    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while True:
        await pilot.wait_for_scheduled_animations()
        if until():
            return
        if loop.time() >= deadline:
            raise TimeoutError("Textual screen transition condition was not reached before timeout")
        await asyncio.sleep(0)
