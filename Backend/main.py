from fastapi import FastAPI, UploadFile, Response
from .modules.stars.services import load_around_position, load_around_id
from .modules.stars.models import (
    SurroundingsIdRequest,
    SurroundingsPosRequest,
    SurroundingsPosResponse,
    SurroundingsIdResponse,
)
from .modules.exoplanets.services import find_exoplanets_by_name, find_some_exoplanets
from .modules.exoplanets.models import ExoplanetsByNameRequest, ExoplanetsResponse
from .modules.input.models import InputResponse
from .modules.input.services import process_input
from .modules.users.models import (
    AuthRequest,
    AuthResponse,
    AllConstellationsRequest,
    ConstellationsResponse,
    ActiveConstellationsRequest,
    ConstellationsResponse,
    CreateConstellationRequest,
    CreateConstellationResponse,
)
from .modules.users.services import (
    registerUser,
    loginUser,
    createConstellation,
    getAllConstellationsByUser,
    getActiveConstellationsByUser,
)
from .modules.admin.services import (
    start_db,
)


app = FastAPI()
start_db()

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
) -> ExoplanetsResponse:
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
async def register(request: AuthRequest) -> AuthResponse:
    user_id = await registerUser(request)
    return AuthResponse(user_id=user_id)


@app.post("/login")
async def login(request: AuthRequest) -> AuthResponse:
    user_id = await loginUser(request)
    return AuthResponse(user_id=user_id)


@app.post("/create_constellation")
async def create_constellation(request: CreateConstellationRequest) -> CreateConstellationResponse:
    message = await createConstellation(request.user_id, request.constellation)
    return CreateConstellationResponse(message=message) 


@app.post("/list_all_constellations")
async def list_all_constellations(
    request: AllConstellationsRequest,
) -> ConstellationsResponse:
    constellations = await getAllConstellationsByUser(request.user_id)
    return ConstellationsResponse(constellations=constellations)


@app.post("/list_active_constellations")
async def list_active_constellations(
    request: ActiveConstellationsRequest,
) -> ConstellationsResponse:
    constellations = await getActiveConstellationsByUser(
        request.user_id, request.ra, request.dec, request.dist
    )
    return ConstellationsResponse(constellations=constellations)


@app.post("/admin/init_db")
def init_db():
    start_db()