from fastapi import UploadFile
from .models import Action
import numpy as np
import cv2
from .processor import process_gesture

async def process_input(file: UploadFile) -> str:
    file_bytes = await file.read()

    np_array = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    cv2.imwrite("image.jpg", img)
    action = process_gesture(img)

    return action
