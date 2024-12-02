import os
from typing import Dict
from supabase import create_client, Client
from functools import lru_cache
from .document_processing import logger


class Storage:
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL")
        self.key: str = os.environ.get("SUPABASE_KEY")
        self.table_name = "LandSearch"
        self.supabase: Client = None

        # Connect to client
        self.__connect_client()

    @lru_cache(maxsize=None)
    def __connect_client(self):
        if not self.url or not self.key:
            logger.warning("Supabase URL or API Key not set.")
            raise Exception("Supabase URL or API Key not set.")
        else:
            self.supabase = create_client(self.url, self.key)

    def get_data(self) -> Dict:
        response = self.supabase.table(self.table_name).select("*").execute()
        return response.data

    def store_data(self, data: Dict) -> Dict:
        try:
            payload: Dict = {"data": data}
            response = self.supabase.table(self.table_name).insert(payload).execute()
        except Exception as e:
            logger.warning(f"Could not save site data {str(e)}")
            return None
        else:
            return response
