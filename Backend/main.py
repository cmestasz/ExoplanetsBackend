from fastapi import FastAPI, UploadFile, Response
from urllib3.response import HTTPResponse
from .modules.stars.services import load_around_position, load_around_id
from .modules.stars.models import (
    SurroundingsIdRequest,
    SurroundingsPosRequest,
    SurroundingsPosResponse,
    SurroundingsIdResponse,
)
from .modules.exoplanets.services import find_exoplanets_by_name, find_some_exoplanets
from .modules.exoplanets.models import ExoplanetsByNameRequest, RequestExoplanets
from .modules.input.models import InputResponse
from .modules.input.services import process_input
from .modules.users.models import (
    ConstellationsResponse,
    ActiveConstellationsRequest,
    ConstellationsResponse,
    CreateConstellationRequest,
    CreateConstellationResponse,
)
from .modules.users.services import (
    createConstellation,
    getAllConstellationsByUser,
    getActiveConstellationsByUser,
)
from supabase import create_client, Client, ClientOptions, AClient
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
import os, json
from dotenv import load_dotenv


load_dotenv()
app = FastAPI()

language = "es"
error = False
error_message = ""

SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_KEY = os.getenv("SUPABASE_KEY")

active_websockets = {}

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=ClientOptions(
    flow_type="pkce"
))


@app.post("/load_surroundings")
async def load_surroundings(request: SurroundingsPosRequest) -> SurroundingsPosResponse:
    stars = await load_around_position(request.ra, request.dec, request.dist)
    return SurroundingsPosResponse(stars=stars)


@app.post("/load_surroundings_by_id")
async def load_surroundings_by_id(
    request: SurroundingsIdRequest,
) -> SurroundingsIdResponse:
    stars, name, ra, dec, dist = await load_around_id(request.id)
    return SurroundingsIdResponse(stars=stars, name=name, ra=ra, dec=dec, dist=dist)


@app.post("/get_exoplanets_by_name")
async def get_exoplanets_by_name(
    request: ExoplanetsByNameRequest,
)-> JSONResponse :
    exoplanets:str = await find_exoplanets_by_name(request.name)
    return JSONResponse(content=exoplanets, status_code=200)


@app.post("/get_some_exoplanets")
async def get_some_exoplanets(request: RequestExoplanets):
    if request.index==None or not request.amount:
        return HTTPException(status_code=400, detail="Exoplanet's index and amount needed")
    status, exoplanets= await find_some_exoplanets(request.index, request.amount)
    if not status: 
        return HTTPException(status_code=400, detail="Error in request to ExoplanetArchive")
    return JSONResponse(content=exoplanets, status_code=200)


@app.post("/get_action")
async def get_action(file: UploadFile) -> InputResponse:
    cursor, r_gesture, rotation, zoom = await process_input(file)
    return InputResponse(cursor=cursor, right_gesture=r_gesture, rotation=rotation, zoom=zoom)

@app.post("/create_constellation")
async def create_constellation(request: CreateConstellationRequest) -> CreateConstellationResponse:
    message = await createConstellation(request.user_id, request.constellation)
    return CreateConstellationResponse(message=message) 


@app.post("/list_all_constellations")
async def list_all_constellations(request: Request) -> ConstellationsResponse:
    constellations = await getAllConstellationsByUser()
    return ConstellationsResponse(constellations=constellations)


@app.post("/list_active_constellations")
async def list_active_constellations(
    request: ActiveConstellationsRequest,
) -> ConstellationsResponse:
    constellations = await getActiveConstellationsByUser(
        request.ra, request.dec, request.dist, request.jwt
    )
    return ConstellationsResponse(constellations=constellations)

@app.get("/login")
def login(request: Request):

    lang = request.query_params.get("lang")

    if lang == "en":
        global language
        language = lang

    try:
        redirect_url = "http://localhost:8000/callback"
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })  
    except Exception as e:
        global error
        error = True
        error_message = f"Error during login: {str(e)}"
    finally:
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
    try:
        code = request.query_params.get("code")
        response = supabase.auth.exchange_code_for_session({
            "auth_code": code,
        })

        token = response.session.access_token
        refresh_token = response.session.refresh_token
        url = f"http://localhost:8000/success?token={token}&refresh_token={refresh_token}"
        return RedirectResponse(url=url) 
    except Exception as e:
        global error
        error = True
        error_message = f"Error during callback: {str(e)}"
        return RedirectResponse(url=url) 

@app.get("/success")
async def success (request: Request):
    token = request.query_params.get("token")
    refresh_token = request.query_params.get("refresh_token")

    global error
    global langugage

    file_path = f"./{language}.json"

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = data["auth_page"]

    if token is None and refresh_token is None:
        error = True
        error_message = "Token or refresh token not found in query parameters"

    if "client_channel" in active_websockets:
        websocket : WebSocket = active_websockets["client_channel"]
        await websocket.send_json({ "token": token, "refresh_token": refresh_token })
    else:
        error = True
        error_message = "WebSocket connection not found"

    title = data["error"]["title"] if error else data["success"]["title"]
    main_message = data["error"]["main_message"] if error else data["success"]["main_message"]
    sub_message = data["error"]["sub_message"] if error else data["success"]["sub_message"]
    repo = data["repo"]
    email = data["email"]

    css = """
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        a:visited {
            color: inherit;
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
        }

        .icon-container:hover {
            color: var(--primary);
        }
    </style>
    """

    html_template = f"""
    <html>
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <script src="https://kit.fontawesome.com/f77f33c6ae.js" crossorigin="anonymous"></script>
            <link href="https://fonts.googleapis.com/css2?family=Audiowide&family=Exo+2:ital,wght@0,100..900;1,100..900&family=Orbitron:wght@400..900&display=swap" rel="stylesheet">
            <title>{title}</title>
            {css}
        </head>
        <body>
            <h1>{main_message}</h1>
            <h3>{sub_message}</h3>
            <div class="links">
                <div class="icon-container">
                    <i class="fa-brands fa-github icon-s"></i>
                    <a href="https://github.com/cmestasz/Exoplanets">{repo}</a>
                </div>
                <div class="icon-container">
                    <i class="fa-regular fa-envelope icon-s"></i>
                    <a href="mailto:lgsc21211@gmail.com">{email}</a>
                </div>
            </div>
        </body>
    </html>
    """

    return HTMLResponse(content=html_template, status_code=200, media_type="text/html; charset=utf-8")

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
