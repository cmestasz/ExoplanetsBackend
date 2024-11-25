from fastapi import UploadFile
import numpy as np
import cv2
import mediapipe as mp
from .processor import get_gesture
from .models import *

left_tracker = {
    "label": "none",
    "counter_click": 0,
    "counter_no_click": 0,
    "reference": [0, 0, 0],
    "last_mode": "none",
}

right_tracker = {
    "label": "none",
    "counter_click": 0,
}

hands = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)


async def process_input(file: UploadFile) -> tuple[Cursor, str, Rotation, float]:
    file_bytes = await file.read()

    np_array = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    send = get_gesture(left_tracker, right_tracker, img,  hands)

    cursor = send['cursor'] if 'cursor' in send else Cursor()
    r_gesture = send['right_gesture'] if 'right_gesture' in send else "none"
    rotation = send['rotation'] if 'rotation' in send else Rotation()
    zoom = send['zoom'] if 'zoom' in send else 0.0

    return cursor, r_gesture, rotation, zoom
