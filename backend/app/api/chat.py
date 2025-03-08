# 导入 FastAPI 所需模块和相关依赖
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from app.services.model_service import ModelService  # 导入模型服务，用于生成回复
from app.context import get_service_context          # 获取依赖注入的服务上下文
import re                                          # 正则表达式模块，用于提取课程信息
import logging                                     # 日志模块
import json                                        # JSON 序列化模块

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建 APIRouter 实例，管理路由
router = APIRouter()
# 初始化模型服务实例
model_service = ModelService()


# 定义用于表示聊天消息的数据模型，包含角色和内容
class ChatMessage(BaseModel):
    role: str       # 消息角色，如 "user" 或 "assistant"
    content: str    # 消息内容


# 定义聊天请求的数据模型，包含一组聊天消息
class ChatRequest(BaseModel):
    messages: List[ChatMessage]   # 聊天记录列表


# 定义聊天响应的数据模型，包含回复内容和可选的来源列表
class ChatResponse(BaseModel):
    response: str           # 模型生成的回复
    sources: List[dict] = []  # 可选的来源信息，默认为空列表


# 辅助函数：从消息中提取可能的课程名称
def extract_course_reference(message: str) -> str:
    """从消息中提取可能的课程名称"""
    # 定义几种常见的课程引用模式（正则表达式）
    patterns = [
        r"(?:in|for|my|the)\s+([a-zA-Z\s]+(?:class|course))",
        r"(?:in|for|my|the)\s+([a-zA-Z\s]+)\s+(?:class|course)",
        r"([a-zA-Z\s]+(?:class|course))",
        r"([a-zA-Z\s]+)\s+assignments"
    ]
    # 遍历正则表达式模式，匹配消息内容（先转换为小写）
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            # 找到匹配则返回匹配内容，并去除首尾空格
            return match.group(1).strip()
    # 如果都没有匹配上，则返回空字符串
    return ""


# 定义聊天接口，处理 POST 请求，路径为 "/"
@router.post("/")
async def chat(request: ChatRequest,
               services: dict = Depends(get_service_context)):
    """聊天接口，允许模型调用相关服务函数"""
    try:
        # 获取用户最新一条消息内容
        user_message = request.messages[-1].content
        logger.info(
            f"\n=== New Chat Request ===\nReceived message: {user_message}"
        )

        # 从依赖注入的服务上下文中获取 Canvas 服务和 Stevens 服务实例
        canvas_service = services["canvas_service"]
        stevens_service = services["stevens_service"]

        # 复制当前聊天记录，用于后续传递给模型
        conversation_history = request.messages.copy()

        # 调用模型服务生成初始回复
        model_response = model_service.generate_response(request.messages)
        # 如果模型返回的类型不是字典，说明没有调用任何函数（或者返回异常结果）
        if not isinstance(model_response, dict):
            logger.error(
                f"Unexpected model response type: {type(model_response)}. Response: {model_response}"
            )
            return ChatResponse(response="Unexpected response from model.")

        # 记录初始的模型回复（包含函数调用信息）
        logger.info(
            f"\nInitial LLM response: {json.dumps(model_response, indent=2)}"
        )

        # 初始化重试次数与最大尝试次数
        attempts = 0
        max_attempts = 5
        # 当模型回复为字典且包含 "function" 键时，进入循环处理函数调用
        while isinstance(model_response, dict) and "function" in model_response and attempts < max_attempts:
            attempts += 1
            logger.info(f"Processing function call attempt {attempts}")

            # 从模型回复中提取要调用的函数名称
            function_name = model_response["function"]
            try:
                # 尝试解析函数调用的参数
                arguments = model_response["arguments"]
                # 如果参数为字符串，则使用 JSON 解析
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Error parsing arguments: {str(e)}. Arguments: {model_response['arguments']}"
                )
                return ChatResponse(response="Invalid arguments.")

            logger.info(f"Function call: {function_name} with arguments: {arguments}")

            # 初始化函数调用的结果变量
            function_result = None

            # 根据不同的函数名称执行相应的服务调用
            if function_name == "get_course_assignments":
                # 提取课程标识符（课程代码或名称）
                course_identifier = arguments["course_identifier"]
                logger.info(f"Getting assignments for course : {course_identifier}")
                # 调用 Canvas 服务获取该课程的作业
                assignments = canvas_service.get_assignments_for_course(course_identifier)
                logger.info(f"Got assignments response: {assignments}")
                if assignments:
                    # 如果获取到了作业，格式化返回结果
                    function_result = canvas_service.format_assignments_response(assignments)
                    logger.info(f"Formatted assignments: {function_result}")
                else:
                    # 如果没有找到作业，返回提示信息
                    function_result = f"No assignments found for {course_identifier}."
                    logger.info("No assignments found")

            # 获取所有课程的即将到期作业
            elif function_name == "get_upcoming_courses_assignments":
                all_assignments = []
                try:
                    # 调用 Canvas 服务获取所有课程的即将到期作业
                    all_assignments = canvas_service.get_upcoming_assignments()
                    if all_assignments:
                        function_result = canvas_service.format_assignments_response(all_assignments)
                        logger.info(f"Formatted assignments: {function_result}")
                    else:
                        function_result = f"No assignments found for {course_identifier}."
                        logger.info("No assignments found")
                except Exception as e:
                    logger.error(f"Error getting upcoming assignments: {str(e)}")

                # 如果获取到了作业，再次尝试格式化所有课程的作业信息
                if all_assignments:
                    try:
                        function_result = canvas_service.format_assignments_response({"courses": all_assignments})
                        logger.info(f"Formatted all assignments: {function_result}")
                    except Exception as e:
                        logger.error(f"Error formatting assignments: {str(e)}")
                        function_result = "Error formatting assignments."
                else:
                    function_result = "No upcoming assignments found in any courses."
                    logger.info("No assignments found in any courses")

            # 处理学术日历事件查询
            elif function_name == "get_academic_calendar_event":
                # 根据传入的事件类型参数调用 Stevens 服务获取日历事件信息（支持异步调用）
                function_result = await stevens_service.get_calendar_event(arguments.get("event_type", ""))

            # 处理学位项目要求查询
            elif function_name == "get_program_requirements":
                # 提取项目名称参数
                program_name = arguments["program"]
                # 调用 Stevens 服务获取该项目的课程要求信息（支持异步调用）
                function_result = await stevens_service.get_program_requirements(program_name)

            # 将函数调用返回的结果转换为字符串，如果是 dict 或 list，则使用 JSON 序列化
            function_result_str = json.dumps(function_result) if isinstance(function_result, (dict, list)) else function_result

            # 将函数调用结果以聊天消息的形式加入对话历史，角色为 "assistant"
            conversation_history.append(ChatMessage(role="assistant", content=function_result_str))

            # 将更新后的对话历史再次传给模型，以生成下一个回复
            model_response = model_service.generate_response(conversation_history, function_result_str)
            logger.info(f"Next LLM response: {model_response}")

        # 如果重试次数用完后模型回复仍为字典，则说明无法处理请求，返回错误消息
        if isinstance(model_response, dict):
            return ChatResponse(response=f"Error: Unable to process request after {max_attempts} attempts")
        # 否则返回最终生成的回复
        return ChatResponse(response=model_response)

    except Exception as e:
        # 捕获所有异常，记录错误日志，并返回 HTTP 500 错误
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
