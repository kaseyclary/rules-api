from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

class SupabaseSettings(BaseModel):
    SUPABASE_URL: str = Field(default=os.getenv("SUPABASE_URL"))
    SUPABASE_KEY: str = Field(default=os.getenv("SUPABASE_KEY"))
    SUPABASE_SECRET: str = Field(default=os.getenv("SUPABASE_SECRET"))

    @classmethod
    def get_settings(cls) -> "SupabaseSettings":
        settings = cls()
        # Validate required settings
        if not all([settings.SUPABASE_URL, settings.SUPABASE_KEY]):
            raise ValueError(
                "Missing required Supabase settings. Please ensure SUPABASE_URL and SUPABASE_KEY "
                "are set in your environment variables."
            )
        return settings

    def get_client(self) -> Client:
        """Create and return a Supabase client instance."""
        return create_client(
            supabase_url=self.SUPABASE_URL,
            supabase_key=self.SUPABASE_KEY
        )

# Create a singleton instance of settings
settings = SupabaseSettings.get_settings()

# Create a singleton instance of the Supabase client
supabase = settings.get_client()