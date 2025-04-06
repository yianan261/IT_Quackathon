from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse  # 添加这行
from app.services.cosmos_service import CosmosService
from app.models.student import Student
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/")
async def create_student(student: Student):
    try:
        # 转换为字典
        student_dict = student.model_dump()
        logger.info(f"Converting student to dict: {student_dict}")
        
        # 确保 id 字段存在
        if 'id' not in student_dict:
            student_dict['id'] = student_dict['studentId']
        logger.info(f"Final student data to save: {student_dict}")
        
        # 创建 CosmosService 实例并保存数据
        cosmos_service = CosmosService()
        result = await cosmos_service.save_student(student_dict)
        logger.info(f"Successfully saved student: {result}")
        
        return {
            "message": "Student information saved successfully",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error saving student: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{student_id}")
async def get_student(student_id: str):
    try:
        logger.info(f"Attempting to get student with ID: {student_id}")
        cosmos_service = CosmosService()
        student = await cosmos_service.get_student_by_id(student_id)
        
        if not student:
            logger.info(f"Student not found: {student_id}")
            return JSONResponse(
                status_code=404,
                content={"message": f"Student not found: {student_id}"}
            )
            
        logger.info(f"Successfully retrieved student: {student}")
        return student
        
    except Exception as e:
        logger.error(f"Error getting student: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))