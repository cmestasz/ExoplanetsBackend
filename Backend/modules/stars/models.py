from pydantic import BaseModel


class Star(BaseModel):
    x: str
    y: str
    z: str
    name: str


class SurroundingsPosRequest(BaseModel):
    ra: float
    dec: float
    dist: float


class SurroundingsIdRequest(BaseModel):
    id: str


class SurroundingsPosResponse(BaseModel):
    error: str
    stars: list[Star]


class SurroundingsIdResponse(BaseModel):
    error: str
    stars: list[Star]
    name: str
    ra: float
    dec: float
    dist: float
