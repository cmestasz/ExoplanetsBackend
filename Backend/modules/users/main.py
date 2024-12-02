from supabase import create_client, Client, ClientOptions, AClient
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

JWT_KEY = os.getenv("JWT_KEY")
ALGORITHM = "HS256"

app = FastAPI()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=ClientOptions(
    flow_type="pkce"
))

code = "9894dfca-694a-488a-9632-3ef6a9bf2322"

response = supabase.auth.exchange_code_for_session({
    "auth_code": code,
})


async def o():
    response = supabase.auth.exchange_code_for_session({
        "auth_code": code,
        "code_verifier": "google",
    })
    return response


print(o())