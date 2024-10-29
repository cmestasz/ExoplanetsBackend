from pydantic import BaseModel


class Exoplanet(BaseModel):
    name: str
    ra: float
    dec: float
    parallax: float


class ExoplanetsByNameRequest(BaseModel):
    name: str


class ExoplanetsResponse(BaseModel):
    exoplanets: list[Exoplanet]
