from supabase import create_client, Client
from .config import supabase_settings
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class SupabaseConnection:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            try:
                self._client = create_client(
                    supabase_settings.SUPABASE_URL,
                    supabase_settings.SUPABASE_PUBLIC_KEY
                )
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                raise

    @property
    def client(self) -> Client:
        return self._client

    @contextmanager
    def get_client(self) -> Client:
        try:
            yield self.client
        except Exception as e:
            logger.error(f"Error during Supabase operation: {str(e)}")
            raise

supabase = SupabaseConnection()