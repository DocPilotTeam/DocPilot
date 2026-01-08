from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
try:
    user = supabase.auth.get_user()
    print("Connected to Supabase!")
except Exception as e:
    print("Failed to connect to Supabase:", e)

