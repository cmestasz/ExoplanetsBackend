from pydantic import BaseModel
from enum import Enum

class Action(Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"


class InputResponse(BaseModel):
    action: str
