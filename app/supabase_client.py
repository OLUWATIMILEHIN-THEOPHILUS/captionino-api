# Connect to supabase here.
from supabase import create_client
from .config import settings

SUPABASE_URL = settings.supabase_project_url
SUPABASE_ANON_KEY = settings.supabase_api_key

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
