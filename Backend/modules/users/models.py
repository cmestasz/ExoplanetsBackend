from pydantic import BaseModel

class AuthResponse (BaseModel): 
    username: str
    message: str

class AuthRequest (BaseModel):
    username: str
    password: str
