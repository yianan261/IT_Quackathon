# Stevens AI Assistant

## Quick Start with Docker (Development)

1. Clone the repository:

```bash
git clone git@github.com:yianan261/IT_Quackathon.git
cd IT_Quackathon
```

2. Create a `.env` file with your credentials:

```env
CANVAS_API_URL=https://sit.instructure.com/api/v1/
CANVAS_API_KEY=your_canvas_key
OPENAI_API_KEY=your_openai_key
COSMOSDB_URI=your_cosmos_uri
COSMOSDB_KEY=your_cosmos_key
COSMOSDB_DATABASE=stevens-ai
```

3. Build and run with Docker Compose:

```bash
docker-compose up --build
```

4. Access the API at http://localhost:8000

## Testing the API

Test the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/chat \
-H "Content-Type: application/json" \
-d '{
  "messages": [{
    "role": "user",
    "content": "What are my upcoming assignments for {class_name} class?"
  }]
}'
```

Alternatively test on Postman

### To run without Docker:

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the server:

```bash
uvicorn main:app --reload
```

### Project Structure

See project structure file (subject to updates)
