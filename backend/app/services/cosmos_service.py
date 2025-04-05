from azure.cosmos import CosmosClient
from app.core.config import settings

class CosmosService:
    def __init__(self):
        self.client = CosmosClient(settings.COSMOS_URI, settings.COSMOS_KEY)
        self.database = self.client.get_database_client(settings.COSMOS_DATABASE)
        self.container = self.database.get_container_client(settings.COSMOS_CONTAINER)

    async def save_student(self, student_data: dict):
        try:
            return self.container.create_item(body=student_data)
        except Exception as e:
            print(f"Error saving to Cosmos DB: {str(e)}")
            raise