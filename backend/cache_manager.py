import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import json

try:
    import redis
except ImportError:
    logging.error("Redis package not installed. Please run: pip install redis")
    raise


class CacheManager:

    def __init__(self):
        try:
            self.redis_client = redis.Redis(host='localhost',
                                            port=6379,
                                            db=0,
                                            decode_responses=True)
            if not self.redis_client.ping():
                logging.warning("Redis ping failed, running without cache")
                self.redis_client = None
        except redis.ConnectionError:
            logging.warning(
                "Could not connect to Redis. Running without cache.")
            self.redis_client = None
        except Exception as e:
            logging.error(f"Error initializing Redis client: {str(e)}")
            raise

        self.scheduler = BackgroundScheduler()

    def start_scheduler(self, scraping_function, hours=24):
        """Start the scheduler to periodically update the cache"""
        try:
            self.scheduler.add_job(scraping_function,
                                   'interval',
                                   hours=hours,
                                   id='scraping_job')
            self.scheduler.start()
        except Exception as e:
            logging.error(f"Error starting scheduler: {str(e)}")
            raise

    def get_cached_data(self, key):
        """Retrieve data from cache"""
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logging.error(f"Error retrieving data from cache: {str(e)}")
            return None

    def set_cached_data(self, key, data):
        """Store data in cache"""
        try:
            self.redis_client.set(key, json.dumps(data))
        except Exception as e:
            logging.error(f"Error storing data in cache: {str(e)}")
            raise
