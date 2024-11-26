import cv2
import mediapipe as mp
import numpy as np
import math
from .models import Action

# Inicializamos Mediapipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Función para calcular ángulos entre puntos
def calculate_angle(x1, y1, x2, y2):
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return angle

# Función para calcular distancia entre dos puntos
def calculate_distance(x1, y1, x2, y2):
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Reinicia las acciones de los gestos
def reset_gesture_actions():
    return {
        'move_up': False,
        'move_down': False,
        'move_left': False,
        'move_right': False,
        'zoom_in': False,
        'zoom_out': False,
    }

def process_gesture(image):
    gesture_actions = reset_gesture_actions()
    mode = 'move'  # Cambia este modo según necesites

    with mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8) as hands:
        # Convertimos a RGB para Mediapipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        rgb_image.flags.writeable = False
        results = hands.process(rgb_image)

        # Volvemos a BGR para OpenCV
        rgb_image.flags.writeable = True
        image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)

        # Procesamos las manos detectadas
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Obtenemos las posiciones de los dedos
                landmarks = hand_landmarks.landmark
                index_finger_tip = landmarks[8]
                thumb_tip = landmarks[4]

                # Detectar puño: todos los dedos cerrados excepto el pulgar
                fingers_closed = [landmarks[i].y > landmarks[0].y for i in range(1, 5)]
                thumb_closed = landmarks[4].y > landmarks[3].y

                if thumb_closed and all(fingers_closed):
                    if mode == 'zoom':
                        gesture_actions['zoom_in'] = True

                # Detectar mano abierta: todos los dedos levantados
                fingers_open = [landmarks[i].y < landmarks[0].y for i in range(1, 5)]
                thumb_open = landmarks[4].y < landmarks[3].y

                if thumb_open and all(fingers_open):
                    thumb_dist = calculate_distance(landmarks[4].x, landmarks[4].y, landmarks[0].x, landmarks[0].y)
                    if thumb_dist > 0.1:
                        if mode == 'zoom':
                            gesture_actions['zoom_out'] = True

                # Coordenadas del índice y pulgar
                x_index, y_index = int(index_finger_tip.x * image.shape[1]), int(index_finger_tip.y * image.shape[0])
                x_thumb, y_thumb = int(thumb_tip.x * image.shape[1]), int(thumb_tip.y * image.shape[0])

                # Detectar si el índice está claramente levantado y aislado
                index_angle = calculate_angle(landmarks[6].x * image.shape[1], landmarks[6].y * image.shape[0], x_index, y_index)
                index_to_middle_dist = calculate_distance(landmarks[8].x, landmarks[8].y, landmarks[12].x, landmarks[12].y)

                if index_to_middle_dist > 0.05:
                    if mode == 'move':
                        if -20 <= index_angle <= 20:
                            gesture_actions['move_left'] = True
                        elif 160 <= index_angle <= 180 or -180 <= index_angle <= -160:
                            gesture_actions['move_right'] = True
                        elif 60 < index_angle < 120:
                            gesture_actions['move_down'] = True
                        elif -120 < index_angle < -60:
                            gesture_actions['move_up'] = True

                # Detectar zoom con el pulgar y el índice
                thumb_to_index_dist = calculate_distance(landmarks[4].x, landmarks[4].y, landmarks[8].x, landmarks[8].y)
                if mode == 'zoom':
                    if thumb_to_index_dist < 0.05:
                        gesture_actions['zoom_in'] = True
                    elif thumb_to_index_dist > 0.1 and y_thumb > landmarks[3].y * image.shape[0]:
                        gesture_actions['zoom_out'] = True

    # Aquí podrías retornar la acción correspondiente en función de `gesture_actions`
    if gesture_actions['zoom_in']:
        return Action.ZOOM_IN
    elif gesture_actions['zoom_out']:
        return Action.ZOOM_OUT
    elif gesture_actions['move_up']:
        return Action.UP
    elif gesture_actions['move_down']:
        return Action.DOWN
    elif gesture_actions['move_left']:
        return Action.LEFT
    elif gesture_actions['move_right']:
        return Action.RIGHT
    
    return 'do_nothing'
