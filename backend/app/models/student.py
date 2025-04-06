from pydantic import BaseModel, EmailStr

class Student(BaseModel):
    studentName: str
    studentId: str
    major: str
    academicLevel: str
    email: EmailStr
    
