from supabase import create_client, Client, ClientOptions, AClient
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, HTMLResponse
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
def login():
    redirect_url = "http://localhost:8000/callback"
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": redirect_url
        }
    })
    return RedirectResponse(url=response.url)

@app.post("/logout")
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

    html =  """"
    <html>

    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <script src="https://kit.fontawesome.com/f77f33c6ae.js" crossorigin="anonymous"></script>
        <link
        href="https://fonts.googleapis.com/css2?family=Audiowide&family=Exo+2:ital,wght@0,100..900;1,100..900&family=Orbitron:wght@400..900&display=swap"
        rel="stylesheet">
        <title>{(_error ? _titlePageError : _titlePage)}</title>
    </head>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
        }

        a {
            text-decoration: none;
        }

        a:visited {
            text-decoration: none;
        }

        :root {
            --primary: #E05600;
            --secondary: #C2B51F;
        }

        body {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100dvh;
            padding: 2rem;
            gap: 2rem;
            background-color: black;
            text-align: center;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif
        }

        h1 {
            color: var(--primary);
            font-size: 2.5rem;
            font-family: 'Audiowide';
            line-height: 3rem;
        }

        h2 {
            color: var(--secondary);
            font-family: 'Orbitron';
        }

        h3 {
            font-family: 'Exo 2';
            color: var(--secondary);
            font-size: small;
        }

        .links {
            display: flex;
            gap: 2rem;
            color: var(--secondary);
            font-size: 1.5rem;
        }

        .icon-container {
            color: var(--secondary);
            font-size: small;
            font-weight: 500;
            font-family: 'Exo 2';
            display: flex;
            gap: .4rem;
            align-items: center;

            & a {
            color: var(--secondary);
            }
        }

        .icon-container:hover {
            color: var(--primary);

            & a {
            color: var(--primary);
            }
        }

    </style>

    <body>
        <h1>{(_error ? _mainMessageError : _mainMessage)}</h1>
        <h3>{(_error ? _subMessageError : _subMessage)}</h3>
        <div class="links">
            <div class="icon-container">
            <i class="fa-brands fa-github icon-s"></i>
            <a href="https://github.com/cmestasz/Exoplanets">{_repo}</a>
            </div>
            <div class="icon-container">
            <i class="fa-regular fa-envelope icon-s"></i>
            <a href="mailto:lgsc21211@gmail.com">{_email}</a>
            </div>
        </div>
    </body>

    </html>
    """
    return HTMLResponse(content=html, status_code=200)

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