from __future__ import annotations

import pytest

from textual_sync import wait_for_screen_transition


class DelayedTransitionPilot:
    def __init__(self) -> None:
        self.cycles = 0
        self.transition_complete = False

    async def wait_for_scheduled_animations(self) -> None:
        self.cycles += 1
        if self.cycles >= 2:
            self.transition_complete = True


@pytest.mark.asyncio
async def test_screen_transition_wait_retries_until_condition_is_true() -> None:
    pilot = DelayedTransitionPilot()

    await wait_for_screen_transition(
        pilot,
        until=lambda: pilot.transition_complete,
        timeout=0.5,
    )

    assert pilot.cycles >= 2
