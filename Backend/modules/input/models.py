from pydantic import BaseModel


class Cursor(BaseModel):
    x: float = 0
    y: float = 0


class Rotation(BaseModel):
    dx: float = 0
    dy: float = 0


class InputResponse(BaseModel):
    cursor: Cursor
    right_gesture: str
    rotation: Rotation
    zoom: float
