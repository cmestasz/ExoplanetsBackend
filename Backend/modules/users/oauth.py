from supabase import create_client, Client, ClientOptions, AClient
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

JWT_KEY = os.getenv("JWT_KEY")
ALGORITHM = "HS256"

active_websockets = {}

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

@app.get("/logout")
async def logout ():
    if "client_channel" in active_websockets:
        websocket: WebSocket = active_websockets["client_channel"]
        await websocket.close()
        active_websockets.pop("client_channel", None)
        print("WebSocket connection closed.")

    try:
        supabase.auth.sign_out()
    except:
        raise HTTPException(status_code=500, detail="Error during logout")
    
    return {"message": "Logout successful", "status": 200}

@app.get("/callback")
def callback(request: Request):
    code = request.query_params.get("code")
    response = supabase.auth.exchange_code_for_session({
        "auth_code": code,
    })

    token = response.session.access_token
    refresh_token = response.session.refresh_token
    url = f"http://localhost:8000/success?token={token}&refresh_token={refresh_token}"

    return RedirectResponse(url=url)    

@app.get("/success")
async def success (request: Request):
    token = request.query_params.get("token")
    refresh_token = request.query_params.get("refresh_token")

    if token is None or refresh_token is None:
        return "Invalid token"
    if "client_channel" in active_websockets:
        websocket : WebSocket = active_websockets["client_channel"]
        await websocket.send_json({ "token": token, "refresh_token": refresh_token })
    else:
        raise HTTPException(status_code=400, detail="No active WebSocket connection for the client channel.")

    return f"Token sent to client WebSocket: {token}"

@app.websocket("/login_flow")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    active_websockets["client_channel"] = websocket

    try:
        while True:
            message = await websocket.receive_text()
            if message == "token_received":
                print("Client confirmed token reception. Closing WebSocket...")
                break 
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        active_websockets.pop("client_channel", None)