from fastapi import FastAPI, UploadFile, HTTPException, APIRouter
from .modules.stars.services import generate_around_planet_name, load_around_position, load_around_id
from .modules.stars.models import SurroundingsIdRequest, SurroundingsRequest, SurroundingsResponse, NameRequest
from .modules.exoplanets.services import find_exoplanets_by_name, find_some_exoplanets
from .modules.exoplanets.models import ExoplanetsByNameRequest, ExoplanetsResponse
from .modules.input.models import InputResponse
from .modules.input.services import process_input
from .modules.users.models import AuthRequest, AuthResponse, Constellation
from .modules.users.services import registerUser, loginUser, init_bd, createConstellation, getConstellationsByUser

app = FastAPI()
router = APIRouter()
init_bd()


@app.post("/load_surroundings")
async def load_surroundings(request: SurroundingsRequest) -> SurroundingsResponse:
    stars = await load_around_position(request.ra, request.dec, request.dist)
    return SurroundingsResponse(stars=stars)


@app.post("/load_surroundings_by_id")
async def load_surroundings_by_id(request: SurroundingsIdRequest) -> SurroundingsResponse:
    stars = await load_around_id(request.id)
    return SurroundingsResponse(stars=stars)


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
    action = await process_input(file)
    return InputResponse(action=action)

@app.post("/register")
async def register (request: AuthRequest) -> AuthResponse:
    return registerUser(request)

@app.post("/login")
async def login (request: AuthRequest) -> AuthResponse:
    return loginUser(request)

@router.post("/users/{user_id}/constellations", response_model=dict)
async def add_constellation(user_id: int, constellation: Constellation):
    return await createConstellation(user_id, constellation)

@router.get("/users/{user_id}/constellations", response_model=list[Constellation])
async def list_constellations(user_id: int):
    constellations = await getConstellationsByUser(user_id)
    if not constellations:
        raise HTTPException(status_code=404, detail="No constellations found for this user")
    return constellations

app.include_router(router, prefix="/api/v1")