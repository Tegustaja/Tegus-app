from supabase import create_client, Client
import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
	try:
		supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
	except Exception:
		supabase = None


def get_data(table_name: str, row: str = "messages", id: str = "NULL"):
	try:
		if not supabase:
			return []
		response = supabase.table(table_name).select(row).eq("session_id", id).execute()
		return response.data
	except Exception as e:
		return e


def insert_data(table_name: str = "lesson_sessions", update: dict | str = "NULL", id: str = "NULL"):
	try:
		if not supabase:
			return {"error": "Supabase client not configured"}
		response = supabase.table(table_name).update(update).eq("session_id", id).execute()
		return response
	except Exception as e:
		return e

