from pydantic import BaseModel


class Exoplanet(BaseModel):
    name: str
    ra: float
    dec: float
    parallax: float


class ExoplanetsByNameRequest(BaseModel):
    name: str

class RequestExoplanets(BaseModel):
    index: int | None
    amount: int | None

class ExoplanetsResponse(BaseModel):
    exoplanets: list[Exoplanet]
