from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.config import settings

client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str= settings.CONN_STR
)

projects = client.projects.list()
for project in projects:
    print(project.name)
