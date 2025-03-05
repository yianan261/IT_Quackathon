from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.stevens_service import StevensService

router = APIRouter()


@router.get("/programs")
async def get_programs(
        db: Session = Depends(get_db),
        stevens_service: StevensService = Depends(StevensService)):
    return stevens_service.get_programs()
