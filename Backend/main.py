from fastapi import FastAPI, UploadFile, HTTPException, APIRouter
from .modules.stars.services import load_around_position, load_around_id
from .modules.stars.models import SurroundingsIdRequest, SurroundingsPosRequest, SurroundingsPosResponse, SurroundingsIdResponse
from .modules.exoplanets.services import find_exoplanets_by_name, find_some_exoplanets
from .modules.exoplanets.models import ExoplanetsByNameRequest, ExoplanetsResponse
from .modules.input.models import InputResponse
from .modules.input.services import process_input
from .modules.users.models import AuthRequest, AuthResponse, AllConstellationsRequest, ConstellationsResponse, ActiveConstellationsRequest, ConstellationsResponse, CreateConstellationRequest, CreateConstellationResponse
from .modules.users.services import registerUser, loginUser, init_bd, createConstellation, getConstellationsByUser, getActiveConstellationsByUser

app = FastAPI()
init_bd()


@app.post("/load_surroundings")
async def load_surroundings(request: SurroundingsPosRequest) -> SurroundingsPosResponse:
    error, stars = await load_around_position(request.ra, request.dec, request.dist)
    return SurroundingsPosResponse(error=error, stars=stars)


@app.post("/load_surroundings_by_id")
async def load_surroundings_by_id(request: SurroundingsIdRequest) -> SurroundingsIdResponse:
    error, stars, name, ra, dec, dist = await load_around_id(request.id)
    return SurroundingsIdResponse(error=error, stars=stars, name=name, ra=ra, dec=dec, dist=dist)


@app.post("/get_exoplanets_by_name")
async def get_exoplanets_by_name(request: ExoplanetsByNameRequest) -> ExoplanetsResponse:
    exoplanets = await find_exoplanets_by_name(request.name)
    return ExoplanetsResponse(exoplanets=exoplanets)


@app.post("/get_some_exoplanets")
async def get_some_exoplanets() -> ExoplanetsResponse:
    exoplanets = await find_some_exoplanets()
    return ExoplanetsResponse(exoplanets=exoplanets)

@app.post("/get_action_by_image")
async def get_action_by_image(file: UploadFile) -> InputResponse:
    error, action = await process_input(file)
    return InputResponse(error=error, action=action)

@app.post("/register")
async def register (request: AuthRequest) -> AuthResponse:
    return registerUser(request)

@app.post("/login")
async def login (request: AuthRequest) -> AuthResponse:
    return loginUser(request)

@app.post("/add_constellation")
async def add_constellation(request: CreateConstellationRequest) -> CreateConstellationResponse:
    error = await createConstellation(request.user_id, request.name, request.stars)
    return CreateConstellationResponse(error=error)

@app.get("/list_all_constellations")
async def list_all_constellations(request: AllConstellationsRequest) -> ConstellationsResponse:
    error, constellations = await getConstellationsByUser(request.user_id)
    return ConstellationsResponse(error=error, constellations=constellations)

@app.get("/list_active_constellations")
async def list_active_constellations(request: ActiveConstellationsRequest) -> ConstellationsResponse:
    error, constellations = await getActiveConstellationsByUser(request.user_id, request.ra, request.dec, request.dist)
    return ConstellationsResponse(error=error, constellations=constellations)