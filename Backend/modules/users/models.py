from pydantic import BaseModel


class AuthResponse(BaseModel):
    username: str
    message: str


class AuthRequest(BaseModel):
    username: str
    password: str


class ConstellationStar(BaseModel):
    id: int
    name: str
    x: float
    y: float
    z: float

    connected_stars: list[int]


class Constellation(BaseModel):
    ra: float
    dec: float
    dist: float
    name: str
    stars: list[ConstellationStar]


class User(BaseModel):
    id: int
    username: str
    password: str
    constellations: list[Constellation]


class AllConstellationsRequest(BaseModel):
    user_id: int


class ConstellationsResponse(BaseModel):
    constellations: list[Constellation]


class ActiveConstellationsRequest(BaseModel):
    user_id: int
    ra: float
    dec: float
    dist: float


class CreateConstellationRequest(BaseModel):
    user_id: int
    name: str
    stars: list[ConstellationStar]

