from pydantic import BaseModel
from enum import Enum

class Cursor(BaseModel):
    x: float
    y: float


class Rotation(BaseModel):
    dx: float
    dy: float

class InputResponse(BaseModel):
    cursor: Cursor
    right_gesture: str
    rotation: Rotation
    zoom: float
