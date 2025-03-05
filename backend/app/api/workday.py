from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, date

router = APIRouter()


class WorkdayEvent(BaseModel):
    date: date
    description: str
    type: str


# navigates to class schedule
@router.get("/class_schedule", response_model=List[WorkdayEvent])
async def get_class_schedule():
    pass


# navigates to financial statement
@router.get("/financial_statement", response_model=List[WorkdayEvent])
async def get_financial_statement():
    pass


# navigates to course registration
@router.get("/course_registration", response_model=List[WorkdayEvent])
async def get_course_registration():
    pass
