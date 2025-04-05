from pydantic import BaseModel

class Student(BaseModel):
    studentName: str
    major: str
    academicLevel: str
    