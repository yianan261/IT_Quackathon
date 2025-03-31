import logging

logger = logging.getLogger(__name__)


class StevensService:

    def __init__(self):
        pass

    async def get_calendar_event(self) -> dict:
        pass

    # upates calendar events to outlook
    async def update_calendar(self, event_type: str) -> str:
        pass

    async def get_program_requirements(self, program: str) -> dict:
        pass
