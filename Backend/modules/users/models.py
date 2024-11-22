from pydantic import BaseModel


class AuthResponse(BaseModel):
    user_id: int


class AuthRequest(BaseModel):
    username: str
    password: str


class ConstellationStar(BaseModel):
    ext_id: str
    connected_stars: list[str]


class Constellation(BaseModel):
    ra: float
    dec: float
    dist: float
    id: int
    name: str
    stars: list[ConstellationStar]


class User(BaseModel):
    id: int
    username: str
    password: str


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
    constellation: Constellation


class CreateConstellationResponse(BaseModel):
    message: str
