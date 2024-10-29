from fastapi import FastAPI, UploadFile
from .modules.stars.services import generate_around_planet_name, load_around_position
from .modules.stars.models import SurroundingsRequest, SurroundingsResponse, NameRequest
from .modules.exoplanets.services import find_exoplanets_by_name, find_some_exoplanets
from .modules.exoplanets.models import ExoplanetsByNameRequest, ExoplanetsResponse
from .modules.input.models import InputResponse
from .modules.input.services import process_input

app = FastAPI()


@app.post("/load_surroundings")
async def load_surroundings(request: SurroundingsRequest) -> SurroundingsResponse:
    stars = await load_around_position(request.ra, request.dec, request.parallax)
    return SurroundingsResponse(stars=stars)


@app.post("/load_stars_by_exoplanet_name")
async def load_surroundings_by_name(request: NameRequest) -> SurroundingsResponse:
    stars = await generate_around_planet_name(request.exoplanet_name)
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
