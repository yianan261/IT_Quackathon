from azure.cosmos import CosmosClient, PartitionKey
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CosmosService:
    def __init__(self):
        # 打印连接信息
        logger.info(f"Initializing CosmosService with endpoint: {settings.COSMOS_ENDPOINT}")
        self.client = CosmosClient(
            url=settings.COSMOS_ENDPOINT,
            credential=settings.COSMOS_KEY
        )
        
        # 获取或创建数据库
        self.database = self.client.create_database_if_not_exists(
            id=settings.COSMOS_DATABASE
        )
        logger.info(f"Connected to database: {settings.COSMOS_DATABASE}")
        
        # 获取或创建容器
        self.container = self.database.create_container_if_not_exists(
            id=settings.COSMOS_CONTAINER,
            partition_key=PartitionKey(path="/studentId")
        )
        logger.info(f"Connected to container: {settings.COSMOS_CONTAINER}")

    async def save_student(self, student_data: dict) -> dict:
        """保存学生信息到 Cosmos DB"""
        try:
            # 打印要保存的数据
            logger.info(f"Attempting to save student data: {student_data}")
            
            # 确保有 id 字段
            if 'id' not in student_data:
                student_data['id'] = student_data['studentId']
            
            # 使用 upsert_item 保存数据
            result = self.container.upsert_item(body=student_data)
            logger.info(f"Successfully saved student data: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error saving student data: {str(e)}", exc_info=True)
            raise

    async def get_student_by_id(self, student_id: str) -> dict:
        """根据学生ID获取学生信息"""
        try:
            # 打印查询信息
            logger.info(f"Attempting to query student with ID: {student_id}")
            
            # 构建查询
            query = "SELECT * FROM c WHERE c.studentId = @studentId"
            parameters = [{"name": "@studentId", "value": student_id}]
            
            # 执行查询
            logger.info(f"Executing query: {query} with parameters: {parameters}")
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # 打印查询结果
            logger.info(f"Query returned {len(items)} items: {items}")
            
            return items[0] if items else None
            
        except Exception as e:
            logger.error(f"Error querying student data: {str(e)}", exc_info=True)
            raise

    async def get_all_students(self) -> list:
        """Get all students from database"""
        try:
            logger.info("Attempting to get all students from database")
            query = "SELECT * FROM c"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            logger.info(f"Retrieved {len(items)} students from database")
            return items
        except Exception as e:
            logger.error(f"Error getting all students: {str(e)}")
            raise

    async def get_student_context(self, student_id: str = None) -> str:
        """Get formatted student context for AI agent"""
        try:
            if student_id:
                # Get specific student
                student = await self.get_student_by_id(student_id)
                if student:
                    # 只保留需要的字段
                    clean_student = {
                        "studentName": student.get('studentName'),
                        "studentId": student.get('studentId'),
                        "major": student.get('major'),
                        "academicLevel": student.get('academicLevel'),
                        "email": student.get('email')
                    }
                    return clean_student
                return "No student information found."
            else:
                # Get all students
                students = await self.get_all_students()
                # 清理每个学生的数据
                clean_students = [{
                    "studentName": s.get('studentName'),
                    "studentId": s.get('studentId'),
                    "major": s.get('major'),
                    "academicLevel": s.get('academicLevel'),
                    "email": s.get('email')
                } for s in students]
                return "\n\n".join([self._format_student_info(s) for s in clean_students])
        except Exception as e:
            logger.error(f"Error getting student context: {str(e)}")
            raise

    def _format_student_info(self, student: dict) -> str:
        """Format student information for AI context"""
        return f"""Student Information:
    - Name: {student.get('studentName', 'N/A')}
    - ID: {student.get('studentId', 'N/A')}
    - Major: {student.get('major', 'N/A')}
    - Academic Level: {student.get('academicLevel', 'N/A')}
    - Email: {student.get('email', 'N/A')}"""