from typing import Any, Dict, Tuple
import math
import statistics

def is_click(hand_landmarks, side:str)-> bool:
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
        middle_hand_y < mean_finger_y
    if (side == 'left'):
        flag = flag and hand_landmarks[4].x > hand_landmarks[3].x
    elif (side == 'right'):
        flag = flag and hand_landmarks[4].x < hand_landmarks[3].x
        

    return flag


def detect_right_gesture(hand_landmarks)-> str:
    if (is_click(hand_landmarks,side="right")): return "click"
    return "none"

def detect_left_gesture(hand_landmarks)->str:
    if (is_click(hand_landmarks,side='left')): return "click"
    return "none"

def process_right_hand(send:Dict[str, Any], right_hand:Dict[str, Any], tracker:Dict[str, Any])-> None:
    gesture: str = detect_right_gesture( right_hand['landmark'].landmark )
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

def get_rotation(landmark, reference:list)-> Tuple[int, int]:
    """
    This function calculates the angular velocity based on the position of the hand. Specifically, it computes the angular velocity by analyzing the movement of the index finger relative to a reference point.

    The reference point is defined by the position of the index finger at the moment of mode switching. This position is paired with a reference distance, which is the distance between the metacarpophalangeal (MCP) joints of the index finger and the pinky.

    Using this reference distance, the function applies a quadratic function to estimate the angular velocity, taking into account the changes in position over time
    """
    reference_distance = reference[2]
    reference_x = reference[0] 
    reference_y = reference[1] 
    cursor_x = landmark[8].x
    cursor_y = landmark[8].y
    dx = (cursor_x - reference_x) / reference_distance
    dy = (cursor_y - reference_y) / reference_distance
    
    # Angular velocity
    dx = dx**2 * 125 / 4
    dy = dy**2 * 125 / 4
    if (cursor_x < reference_x): dx *= -1
    if (cursor_y > reference_y): dy *= -1
    return math.floor(dx), math.floor(dy)

def set_reference(landmark, reference:list)-> None:
    reference[0] = landmark[8].x
    reference[1] = landmark[8].y
    reference[2] = math.sqrt( 
        (landmark[5].x - landmark[17].x)**2 +
        (landmark[5].y - landmark[17].y)**2 
    )
    print(f"reference distance: {reference[2]}")

def process_left_hand(send:Dict[str, Any], left_hand:Dict[str, Any], tracker:Dict[str, Any])-> None:
    gesture: str =detect_left_gesture(left_hand['landmark'].landmark)
    if (tracker['label'] == 'rotation'):
        print('rotation')
        if (gesture=='click'):
            tracker['counter_no_click'] = 0
            dx, dy = get_rotation(left_hand['landmark'].landmark, tracker['reference'])
            print(f"{dx}\n{dy}")
            send['rotation'] = {
                'dx':dx,
                'dy':dy,
            }
        else:
            if (tracker['counter_no_click'] > 10):
                tracker['last_mode'] = 'rotation'
                tracker['label'] = 'switch'
                tracker['counter_click'] = 0
            else: tracker['counter_no_click'] += 1
    elif (tracker['label'] == 'zoom'):
        #if (gesture == 'zoom'):
        print('zoom')
        if (gesture == 'click'):
            tracker['counter_click'] += 1
            if (tracker['counter_click'] > 30):
                tracker['last_mode'] = 'zoom'
                tracker['label'] = 'switch'
        else: tracker['counter_click'] = 0

    elif (tracker['label'] == 'switch'):
        if (gesture == 'click'):
            tracker['counter_click'] += 1
            if (tracker['counter_click'] > 15 and 10< tracker['counter_no_click'] < 30):
                if (tracker['last_mode'] == 'rotation'): tracker['label'] = 'zoom'
                else:
                    tracker['label'] = 'rotation'
                    set_reference(left_hand['landmark'].landmark,tracker['reference'])
                tracker['counter_click'] = 0
                tracker['counter_no_click'] = 0
            elif (tracker['counter_click'] > 30):
                tracker['label'] = 'rotation'
            else:
                tracker['counter_no_click'] = 0
        else: 
            if (tracker['counter_no_click'] < 15):
                tracker['counter_no_click'] += 1
            else:
                tracker['counter_click'] = 0
    else:
        if (gesture == 'click'):
            tracker['counter_click'] += 1
            if (tracker['counter_click'] > 10):
                tracker['label'] = 'rotation'
                set_reference(left_hand['landmark'].landmark,tracker['reference'])

