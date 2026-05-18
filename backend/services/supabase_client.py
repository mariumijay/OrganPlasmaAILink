import os
import httpx
from functools import wraps

# SAFE SURGICAL FIX: Intercept __init__ without breaking super() context
def patch_httpx_client(cls):
    orig_init = cls.__init__
    @wraps(orig_init)
    def patched_init(self, *args, **kwargs):
        if 'proxy' in kwargs:
            proxy = kwargs.pop('proxy')
            if proxy and 'proxies' not in kwargs:
                kwargs['proxies'] = proxy
        return orig_init(self, *args, **kwargs)
    cls.__init__ = patched_init

patch_httpx_client(httpx.Client)
patch_httpx_client(httpx.AsyncClient)

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

class SupabaseService:
    """
    Singleton class to manage the Supabase client connection.
    Ensures only one instance of the client is used across the application.
    """
    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")
            
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
                
            cls._instance = create_client(url, key)
        return cls._instance

# Export a helper function to get the client easily
def get_supabase() -> Client:
    return SupabaseService.get_client()
