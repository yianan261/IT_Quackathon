from azure.cosmos import CosmosClient
from app.core.config import settings

DUMMY_COSMOSDB_URI = "https://dummy-cosmos.documents.azure.com:443/"


async def get_cosmos_database():
    """Get or create a database instance"""
    try:
        client = CosmosClient(settings.COSMOSDB_URI
                              if settings.COSMOSDB_URI else DUMMY_COSMOSDB_URI,
                              credential=settings.COSMOSDB_KEY)

        database = client.get_database_client(
            settings.COSMOSDB_DATABASE if settings.
            COSMOSDB_DATABASE else "stevens-db")

        return database
    except Exception as e:
        print(f"Error connecting to CosmosDB: {str(e)}")
        return None
