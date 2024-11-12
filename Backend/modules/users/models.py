from pydantic import BaseModel

class AuthResponse (BaseModel): 
    username: str
    message: str

class AuthRequest (BaseModel):
    username: str
    password: str

class Star (BaseModel) :
    id: int
    name: str
    x: float
    y: float
    z: float

    connected_stars: list[int]

class Constellation (BaseModel) :
    id: int
    name: str
    stars: list[Star]


class User (BaseModel) :
    id: int
    username: str
    password: str
    constellations: list[Constellation]

