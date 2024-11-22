from typing import Any, Dict
import statistics

def is_click(hand_landmarks)-> bool:
    flag = False
    middle_hand_y = statistics.mean([
        hand_landmarks[5].y,
        hand_landmarks[9].y,
        hand_landmarks[13].y,
        hand_landmarks[17].y
    ])
    mean_finger_y = statistics.mean([
        hand_landmarks[12].y,
        hand_landmarks[16].y,
        hand_landmarks[20].y,
    ])
    index_finger_points = [
        hand_landmarks[8].x,
        hand_landmarks[7].x,
        hand_landmarks[6].x,
    ]
    range_index_finger_x = max(index_finger_points) - max(index_finger_points)
    alignment = hand_landmarks[8].y < hand_landmarks[7].y < hand_landmarks[6].y


    flag = alignment and \
        ( -0.07 < range_index_finger_x < 0.07 ) and \
        middle_hand_y < mean_finger_y and \
        hand_landmarks[4].x < hand_landmarks[3].x
        

    return flag

def detect_gesture(hand_landmarks)-> str:
    if (is_click(hand_landmarks)): return "click"
    return "none"

def process_right_hand(send, right_hand, tracker:dict[str, Any])-> None:
    gesture: str = detect_gesture( right_hand['landmark'].landmark )
    #print(gesture)
    if (tracker['label'] == 'none'):
        if (gesture == 'click'):
            tracker['counter_click'] += 1
            tracker['label'] = 'click'
    elif (tracker['label'] == 'click'):
        if (gesture == 'click'):
            tracker['counter_click'] += 1
            if (tracker['counter_click'] > 5):
                tracker['label'] = 'prepare'
        else: 
            tracker['counter_click'] = 0
            tracker['label'] = 'none'
    elif (tracker['label'] == 'prepare'):
        if (gesture == 'click'):
            tracker['counter_click'] += 1
            if (tracker['counter_click'] > 30):
                print('select')
                tracker['label'] = 'select'
                send['right_gesture'] = 'select'
        else: 
            send['right_gesture'] = 'click'
            print ('click')
            tracker['label'] = 'none'
            tracker['counter_click'] = 0
    elif(tracker['label'] == 'select'):
        if (not gesture == 'click'):
            print('deselect')
            send['right_gesture'] = 'deselect'
            tracker['label'] = 'none'
            tracker['counter_click'] = 0
