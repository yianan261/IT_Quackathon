import logging

logger = logging.getLogger(__name__)


class StevensService:

    # TODO: add db, these info will either be stored in db or vector db
    def __init__(self, cosmos_db):
        self.db = cosmos_db

    async def get_calendar_event(self) -> dict:
        pass

    # upates calendar events to outlook
    async def update_calendar(self, event_type: str) -> str:
        pass

    async def get_program_requirements(self, program: str) -> dict:
        pass
