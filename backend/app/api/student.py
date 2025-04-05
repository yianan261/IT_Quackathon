from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

class Student(BaseModel):
    studentName: str
    studentId: str
    major: str
    academicLevel: str
    email: EmailStr

@router.post("/")
async def create_student(student: Student):
    try:
        # 暂时只打印数据，不保存到数据库
        print("Received student information:")
        print(f"Name: {student.studentName}")
        print(f"ID: {student.studentId}")
        print(f"Major: {student.major}")
        print(f"Level: {student.academicLevel}")
        print(f"Email: {student.email}")
        
        return {"message": "Student information received successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))