from supabase import create_client, Client, ClientOptions, AClient
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

app = FastAPI()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/login")
def login ():
    redirect_url = "http://localhost:8000/callback"
    auth_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to={redirect_url}"
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(request: Request):
    return "User logged in successfully"

@app.get("/users")
def getUsers():
    response = supabase.table("users").select("*").execute()
    return response.data
