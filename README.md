# Stevens AI Assistant 🤖

A LangChain-powered AI assistant designed specifically for Stevens Institute of Technology students. The assistant provides access to course information, grades, assignments, Workday navigation, and more through intelligent tool usage.

## 🚀 Features

- **📚 Course Management**: Get current courses, assignments, and grades from Canvas
- **📢 Announcements**: Stay updated with course announcements
- **🎓 Academic Support**: Access program requirements and academic calendar events
- **💼 Workday Integration**: Navigate to registration and financial account pages
- **👥 Advisor Information**: Retrieve advisor contact details
- **🤖 LangChain Agents**: Intelligent tool selection based on natural language queries
- **📊 LangSmith Observability**: Monitor, debug, and improve AI performance
- **🔍 RAG Knowledge Base**: Retrieve information from Stevens-specific documents and policies

## 🛠️ Technology Stack

- **Backend**: FastAPI with Python 3.11+
- **AI Framework**: LangChain with OpenAI GPT-4
- **Browser Automation**: Playwright for Workday integration
- **APIs**: Canvas LTI, Stevens services
- **Database**: Azure Cosmos DB (optional)
- **Package Management**: UV (recommended) or pip

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key
- Canvas API key (for course data)
- Stevens Workday credentials (for navigation features)

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone git@github.com:yianan261/IT_Quackathon.git
cd IT_Quackathon
```

### 2. Create Virtual Environment (using UV - recommended)

```bash
# Create virtual environment
uv venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Required - OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here 
OPENAI_MODEL=gpt-4-turbo-preview
MAX_TOKENS=1000

# Optional - LangSmith Observability
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=stevens-ai-assistant
LANGCHAIN_TRACING_V2=true

# Optional - RAG Configuration
RAG_ENABLED=true
VECTOR_DB_PATH=vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RAG_TOP_K=5

# Optional - Canvas Integration
CANVAS_API_URL=https://sit.instructure.com/api/v1/
CANVAS_API_KEY=your_canvas_api_key_here



```

### 4. Run the Application

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

## 📊 LangSmith Setup (Recommended)

LangSmith provides powerful observability for your AI assistant, allowing you to:
- 🔍 **Debug agent decisions** and tool usage
- 📈 **Monitor performance** and response times  
- 🐛 **Identify errors** and improve reliability
- 📊 **Analyze user interactions** and patterns

### Quick LangSmith Setup:

1. **Sign up** at [smith.langchain.com](https://smith.langchain.com)
2. **Create a new project** called "stevens-ai-assistant"
3. **Get your API key** from the settings
4. **Add to your `.env`**:
   ```env
   LANGSMITH_API_KEY=your_langsmith_api_key_here
   LANGSMITH_PROJECT=stevens-ai-assistant
   LANGCHAIN_TRACING_V2=true
   ```
5. **Restart your application** - tracing will automatically begin!

### View Your Traces:
- Visit [smith.langchain.com](https://smith.langchain.com)
- Select your "stevens-ai-assistant" project  
- See real-time agent executions, tool calls, and performance metrics

## 🔍 RAG Knowledge Base

The RAG (Retrieval-Augmented Generation) system allows the AI assistant to access a knowledge base of Stevens-specific information including:

### 📚 **Pre-loaded Information:**
- **Academic Calendar**: Semester dates, deadlines, breaks
- **Program Requirements**: Course requirements by major
- **Financial Information**: Tuition, fees, payment deadlines
- **Student Services**: Campus resources, support services
- **Faculty Directory**: Department contacts and information

### 🚀 **Features:**
- **Semantic Search**: Find relevant information using natural language
- **Document Chunking**: Intelligent text splitting for better retrieval
- **Metadata Filtering**: Search by category, source, or type
- **Real-time Retrieval**: Get up-to-date information instantly

### 🛠️ **Adding Your Own Documents:**

```python
# Example: Add documents to the knowledge base
from app.services.rag_service import RAGService

rag = RAGService()

# Add documents from a directory
rag.add_documents_from_directory("path/to/stevens/docs")

# Add individual documents
from langchain_core.documents import Document

doc = Document(
    page_content="Your Stevens-specific content here...",
    metadata={"source": "policy_manual", "category": "academic"}
)
rag.add_documents([doc])
```

### 📊 **Knowledge Base Stats:**
Ask the AI: *"How many documents are in the knowledge base?"* to see current statistics.

## 🔧 Docker Setup (Alternative)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the API at http://localhost:8000
```

## 🧪 Testing the API

### Basic Chat Test

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
-H "Content-Type: application/json" \
-d '{
  "messages": [
    {
      "role": "user",
      "content": "What courses am I currently taking?"
    }
  ]
}'
```

### Postman Test

**Method**: `POST`  
**URL**: `http://127.0.0.1:8000/api/chat/`  
**Headers**: `Content-Type: application/json`

**Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Show me my upcoming assignments"
    }
  ]
}
```

## 🛠️ Available Tools

The AI assistant automatically uses these tools based on your queries:

| Tool | Description | Example Query |
|------|-------------|---------------|
| `get_current_courses` | Get enrolled courses | "What classes am I taking?" |
| `get_course_assignments` | Get assignments for specific course | "Show CS115 assignments" |
| `get_grades` | Get grades for all courses | "What are my grades?" |
| `get_announcements_for_all_courses` | Get recent announcements | "Any new announcements?" |
| `navigate_to_workday_registration` | Open Workday registration | "Help me register for courses" |
| `navigate_to_workday_financial_account` | Open financial account | "Show my tuition bill" |
| `get_advisors_info` | Get advisor contacts | "Who is my advisor?" |
| `get_program_requirements` | Get degree requirements | "CS masters requirements?" |
| `get_academic_calendar_event` | Get calendar info | "When is spring break?" |
| `search_stevens_knowledge` | Search knowledge base | "Find information about tuition" |
| `get_stevens_info` | Get specific Stevens info | "Tell me about CS program requirements" |
| `get_rag_stats` | Get knowledge base stats | "How many documents are in the knowledge base?" |

## 📁 Project Structure

```
IT_Quackathon/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py              # Main chat endpoint
│   │   │   └── ...
│   │   ├── core/
│   │   │   └── config.py            # Configuration settings
│   │   ├── services/
│   │   │   ├── model_service.py     # LangChain agent service
│   │   │   ├── user_functions.py    # LangChain tools
│   │   │   ├── canvas_service.py    # Canvas API integration
│   │   │   ├── workday_service.py   # Workday automation
│   │   │   └── stevens_service.py   # Stevens-specific services
│   │   └── context.py               # Dependency injection
│   ├── main.py                      # FastAPI application
│   └── requirements.txt             # Python dependencies
├── DuckingAI/                       # Chrome extension (separate)
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## 🤖 Usage Examples

### Academic Queries
- "What are my current courses?"
- "Show me assignments due this week"
- "What's my grade in Machine Learning?"
- "Any new announcements in my classes?"

### Administrative Tasks
- "Help me register for courses"
- "Show me my financial account"
- "Who is my academic advisor?"
- "When is the add/drop deadline?"

### Program Information
- "What are the requirements for Computer Science masters?"
- "When is finals week?"
- "Tell me about spring break dates"

### Knowledge Base Queries
- "Find information about Stevens tuition and fees"
- "What are the Computer Science course requirements?"
- "Tell me about Stevens student services"
- "When is the add/drop deadline?"

## 🔧 Development

### Adding New Tools

1. Create your tool function in `backend/app/services/user_functions.py`:

```python
@tool
def your_new_tool(parameter: str) -> str:
    """
    Description of your tool.
    
    Args:
        parameter: Description of the parameter
        
    Returns:
        str: JSON string with results
    """
    # Your implementation here
    return json.dumps({"result": "data"})
```

2. Add it to the `all_tools` list:

```python
all_tools = [
    # ... existing tools
    your_new_tool,
]
```

The LangChain agent will automatically have access to your new tool!

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for GPT-4 |
| `OPENAI_MODEL` | ❌ | Model name (default: gpt-4-turbo-preview) |
| `MAX_TOKENS` | ❌ | Max response tokens (default: 1000) |
| `LANGSMITH_API_KEY` | ❌ | LangSmith API key for tracing and monitoring |
| `LANGSMITH_PROJECT` | ❌ | LangSmith project name (default: stevens-ai-assistant) |
| `LANGCHAIN_TRACING_V2` | ❌ | Enable LangSmith tracing (default: true) |
| `RAG_ENABLED` | ❌ | Enable RAG knowledge base (default: true) |
| `VECTOR_DB_PATH` | ❌ | Vector database storage path (default: vector_db) |
| `EMBEDDING_MODEL` | ❌ | Embedding model for RAG (default: sentence-transformers/all-MiniLM-L6-v2) |
| `CHUNK_SIZE` | ❌ | Text chunk size for RAG (default: 1000) |
| `CHUNK_OVERLAP` | ❌ | Text chunk overlap (default: 200) |
| `RAG_TOP_K` | ❌ | Number of docs to retrieve (default: 5) |
| `CANVAS_API_KEY` | ❌ | Canvas API key for course data |
| `CANVAS_API_URL` | ❌ | Canvas API URL |
| `WORKDAY_USERNAME` | ❌ | Stevens username for Workday |
| `WORKDAY_PASSWORD` | ❌ | Stevens password for Workday |
| `COSMOSDB_URI` | ❌ | Azure Cosmos DB connection |
| `COSMOSDB_KEY` | ❌ | Azure Cosmos DB key |

## 🚨 Troubleshooting


### Logs

Enable debug logging to see tool executions:

```bash
# The agent runs with verbose=True by default
# Check terminal output for "[DEBUG]" messages
```

## 🤝 Contributing

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📄 License

This project is developed for Stevens Institute of Technology students and faculty.

---

🎓 **Made with ❤️ for Stevens Institute of Technology students**
