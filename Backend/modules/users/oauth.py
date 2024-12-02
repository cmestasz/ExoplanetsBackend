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

@app.get("/login")
def login ():
    redirect_url = "http://localhost:8000/callback"
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": redirect_url
        }
    })
    return RedirectResponse(url=response.url)



@app.get("/callback")
def callback(request: Request):
    code = request.query_params.get("code")
    response = supabase.auth.exchange_code_for_session({
        "auth_code": code,
    })

    token = response.session.access_token
    url = f"http://localhost:8000/success?token={token}"

    return RedirectResponse(url=url)    

@app.get("/success")
def success (request: Request):
    token = request.query_params.get("token")
    return f"Sucessfully logged in, your token is {token}"
