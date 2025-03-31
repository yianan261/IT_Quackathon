from azure.cosmos import CosmosClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class CosmosDB:

    def __init__(self):
        self.client = CosmosClient.from_connection_string(settings.CONN_STR)
        self.database = self.client.get_database_client(
            settings.COSMOSDB_DATABASE)
        self.container = self.database.get_container_client("stevens-ai")

    async def get_item(self, id: str, partition_key: str):
        try:
            return self.container.read_item(item=id,
                                            partition_key=partition_key)
        except Exception as e:
            logger.error(f"Error getting item from CosmosDB: {str(e)}")
            return None

    async def upsert_item(self, item: dict):
        try:
            return self.container.upsert_item(body=item)
        except Exception as e:
            logger.error(f"Error upserting item to CosmosDB: {str(e)}")
            return None
