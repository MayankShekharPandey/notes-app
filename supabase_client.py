import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Simple direct client initialization
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
service_key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise ValueError("Missing Supabase URL or Key in environment variables")

# Create clients
supabase = create_client(url, key)
service_supabase = create_client(url, service_key)

def get_supabase():
    return supabase

def get_service_supabase():
    return service_supabase