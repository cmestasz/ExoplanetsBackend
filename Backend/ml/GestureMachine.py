from typing import Any, Dict, Tuple
import math
import statistics

def is_click(hand_landmarks, side:str)-> bool:
    """
    Decides if the current hand's position looks like a 'L'

    Checks if the index finger is straight, the thumb is to the side and the rest of finger supported on the palm

    Parameters:
        hand_landmarks: A list containing the current position of the fingers' landmarks.
        side: A string with the values of 'left' or 'right'

    Returns:
        A bool indicating if the hand is in that position
        
    Example:
        >>> is_click(landmark, 'left')
        True
    """
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
        hand_landmarks[10].y > hand_landmarks[6].y
    if (side == 'left'):
        flag = flag and hand_landmarks[4].x > hand_landmarks[3].x
    elif (side == 'right'):
        flag = flag and hand_landmarks[4].x < hand_landmarks[3].x
        

    return flag

def get_rotation(landmark, reference:list)-> Tuple[int, int]:
    """
    Calculates the angular velocity of the index finger relative to a reference point.

    The reference point is defined by the position of the index finger at the moment of mode switching. 
    This position is paired with a reference distance, which is the distance between the metacarpophalangeal (MCP) joints 
    of the index finger and the pinky.

    The function estimates the angular velocity by analyzing the movement of the index finger, using the reference distance 
    and a quadratic function to account for changes in the finger's position over time.

    Parameters:
        landmark: A list containing the current position of the fingers' landmarks.
        reference (list): A list containing the reference distance and the position of the index finger at the moment of mode switching. 
                          The reference distance is calculated from the MCP joints of the index finger and pinky.

    Returns:
        Tuple[int, int]: A tuple containing the estimated angular velocity in two components (x, y).
        
    Example:
        >>> get_rotation(current_landmark, reference_data)
        (10, 15)
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

def get_zoom(landmark) -> float:
    """
    Calculates the percentage of zoom 

    It uses the mean of the fingertips and metacarpophalangeal parth of the hand

    Parameters:
        landmark: A list containing the current position of the fingers' landmarks.

    Returns:
        float: The percentage of zoom
        
    Example:
        >>> get_zoom(landmark)
        95.2322%
    """
    if ( ( (landmark[8].x-landmark[4].x)**2 + (landmark[8].y - landmark[4].y)**2 ) < 0.004):
        return 0
    reference = landmark[5].x - landmark[17].x
    mean_fingers_y = statistics.mean([
        landmark[12].y,
        landmark[8].y,
        landmark[16].y,
        landmark[20].y,
    ])
    mean_hand_y = statistics.mean([
        landmark[5].y,
        landmark[9].y,
        landmark[13].y,
        landmark[17].y,
    ])
    distance = mean_hand_y - mean_fingers_y
    return distance / reference * 100

def get_cursor(landmark)->Dict[str, float]:
    x = ( landmark[8].x-landmark[5].x ) / (abs( landmark[17].x - landmark[5].x ))
    x /=3
    x = round(x+0.5,3)
    if x > 1: x = 1
    if x < 0: x = 0

    mean_mcp_y = statistics.mean([
        landmark[5].y,
        landmark[9].y,
        landmark[13].y,
        landmark[17].y,
    ])
    reference_y =  abs( round( landmark[0].y , 2) - round( mean_mcp_y  , 1))
    range_y = landmark[8].y - landmark[6].y
    y = range_y / reference_y 
    y = -y
    y = 0.5 +y

    if (y < 0): y = 0
    if (y > 1): y = 1
    y = round( y, 3)

    if (y < 0): y = 0
    if (y > 1): y = 1

    
    print(y)
    return {
        'x':x,
        'y':y,
    }

def set_reference(landmark, reference:list)-> None:
    """
    This function calculates a distance of reference to calculate the angular velocity

    Parameters:
        landmarks: A list containing the current position of the fingers' landmarks.
        reference: A list which will save the points of reference

    Returns:
        None, just save the values in the list of reference

    Example:
        >>> set_reference(landmark, reference)
    """
    reference[0] = landmark[8].x
    reference[1] = landmark[8].y
    reference[2] = math.sqrt( 
        (landmark[5].x - landmark[17].x)**2 +
        (landmark[5].y - landmark[17].y)**2 
    )
    print(f"reference distance: {reference[2]}")


def detect_right_gesture(hand_landmarks)-> str:
    """
    This function detects the right hand gestures, actually process just the click gesture

    Parameters:
        hand_landmarks: A list containing the current position of the fingers' landmarks.

    Returns:
        A string with the current hands' gesture

    Example:
        >>> detect_right_gesture(hand_landmarks)
        'click'
    """
    if (is_click(hand_landmarks,side="right")): return "click"
    return "none"

def detect_left_gesture(hand_landmarks)->str:
    """
    This function detects the left hand gestures, actually process just the click gesture

    Parameters:
        hand_landmarks: A list containing the current position of the fingers' landmarks.

    Returns:
        A string with the current hands' gesture

    Example:
        >>> detect_left_gesture(hand_landmarks)
        'click'
    """
    if (is_click(hand_landmarks,side='left')): return "click"
    return "none"

def process_right_hand(send:Dict[str, Any], right_hand:Dict[str, Any], tracker:Dict[str, Any])-> None:
    """
    Models a state machine to handle the following states: 'none', 'click', 'prepare', and 'select'.

    This function processes the right hand's position and updates the state based on tracker data.
    
    Parameters:
        send (Dict[str, Any]): The object to be transformed into JSON and sent/processed further.
        right_hand (Dict[str, Any]): Dictionary containing information about the right hand's position.
        tracker (Dict[str, Any]): Dictionary containing information needed to transition between states.

    Returns:
        None: This function modifies the internal state and possibly sends data, but does not return a value.

    Example:
        >>> process_right_hand(send_data, right_hand_data, tracker_data)

    """
    #get_cursor(right_hand['landmark'].landmark)
    send['cursor'] = get_cursor(right_hand['landmark'].landmark)
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
                #print('select')
                tracker['label'] = 'select'
                send['right_gesture'] = 'select'
        else: 
            send['right_gesture'] = 'click'
            #print ('click')
            tracker['label'] = 'none'
            tracker['counter_click'] = 0
    elif(tracker['label'] == 'select'):
        if (not gesture == 'click'):
            #print('deselect')
            send['right_gesture'] = 'deselect'
            tracker['label'] = 'none'
            tracker['counter_click'] = 0


def process_left_hand(send:Dict[str, Any], left_hand:Dict[str, Any], tracker:Dict[str, Any])-> None:
    """
    Models a state machine to handle the following states: 'rotation', 'click', 'zoom', and 'switch'.

    This function processes the left hand's position and updates the state based on tracker data.
    
    Parameters:
        send (Dict[str, Any]): The object to be transformed into JSON and sent/processed further.
        left_hand (Dict[str, Any]): Dictionary containing information about the right hand's position.
        tracker (Dict[str, Any]): Dictionary containing information needed to transition between states.

    Returns:
        None: This function modifies the internal state and possibly sends data, but does not return a value.

    Example:
        >>> process_right_hand(send_data, left_hand_data, tracker_data)
    """
    gesture: str =detect_left_gesture(left_hand['landmark'].landmark)
    if (tracker['label'] == 'rotation'):
        #print('rotation')
        if (gesture=='click'):
            tracker['counter_no_click'] = 0
            dx, dy = get_rotation(left_hand['landmark'].landmark, tracker['reference'])
            #print(f"{dx}\n{dy}")
            send['rotation'] = {
                'dx':dx,
                'dy':dy,
            }
        else:
            if (tracker['counter_no_click'] > 10):
                tracker['last_mode'] = 'rotation'
                tracker['counter_no_click'] = 0
                tracker['label'] = 'zoom'
                tracker['counter_click'] = 16
            else: tracker['counter_no_click'] += 1
    elif (tracker['label'] == 'zoom'):
        if (gesture == 'click' and tracker['counter_no_click'] > 0):
            tracker['counter_click'] += 1
            if (tracker['counter_click'] > 30):
                tracker['last_mode'] = 'zoom'
                tracker['label'] = 'rotation'
        else: 
            send['zoom'] = get_zoom(left_hand['landmark'].landmark)
            tracker['counter_click'] = 0
            tracker['counter_no_click'] = 1

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

