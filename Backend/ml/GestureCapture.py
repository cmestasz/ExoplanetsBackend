from typing import Any, Dict
import cv2
import mediapipe as mp
import json
import GestureMachine

class GestureCapture:
    def __init__(self, camera_index=0, image_size=(128, 128)):
        """
        Initialize the GestureCapture class with MediaPipe hands and camera setup
        
        Args:
            model_path (str): Path to the trained model (optional)
            camera_index (int): Index of the camera device to use
            image_size (tuple): Size of images for model input
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.image_size = image_size
        
        self.cap = cv2.VideoCapture(camera_index)
            
    def draw_frame(self, frame, landmark):
        self.mp_draw.draw_landmarks(
            frame,
            landmark,
            self.mp_hands.HAND_CONNECTIONS
        )
            
    def preprocess_frame(self, frame):
        """
        Preprocess the frame for better hand detection
        
        Args:
            frame (numpy.ndarray): Input frame from camera
            
        Returns:
            numpy.ndarray: Preprocessed frame
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        frame_rgb = cv2.GaussianBlur(frame_rgb, (5, 5), 0)
        frame_rgb = cv2.equalizeHist(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY))
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_GRAY2RGB)
        
        return frame_rgb


    def send_gesture(self, gesture:Dict) ->None:
        if (not gesture): return
        json_str = json.dumps(gesture, indent=4)
        print(json_str)


    def traking_gestures(self) -> None:
        """
        Turn on the camera and read each frame to analyze the hand position and gesture

        Example:
            >>> traking_gestures() 
        """

        left_tracker: Dict[str, Any] = {
            'label': 'none',
            'counter_click': 0,
            'counter_no_click': 0,
            'reference': [0, 0, 0],
            'last_mode': 'none',
        }

        right_tracker: Dict[str, Any] = {
            'label': 'none',
            'counter_click': 0,
        }



        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            frame = cv2.flip(frame, 1)
            processed_frame = self.preprocess_frame(frame)
            results = self.hands.process(processed_frame)
            pixel_x = frame.shape[1]
            pixel_y = frame.shape[0]


            left_hand: Dict[str, Any] = {}
            right_hand: Dict[str, Any] = {}

            if results.multi_hand_landmarks:
                for hand_landmarks, hand_handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    self.draw_frame(frame=frame, landmark=hand_landmarks)
                    if (hand_handedness.classification[0].label == 'Right'):
                        
                        right_hand = {
                            'landmark': hand_landmarks,
                            'handedness': hand_handedness,
                        }
                    else: 
                        left_hand = {
                            'landmark': hand_landmarks,
                            'handedness': hand_handedness,
                        }
                send: dict[Any, Any] = {}

                if (right_hand):
                    #GestureMachine.process_right_hand()
                    GestureMachine.process_right_hand(send=send,
                                                      right_hand=right_hand,
                                                      tracker=right_tracker)
                    pixel_x *= send['cursor']['x']
                    pixel_y *= send['cursor']['y']
                if (left_hand):
                    GestureMachine.process_left_hand(send=send,
                                                     left_hand=left_hand,
                                                     tracker=left_tracker)

                #self.send_gesture(send)
            cv2.circle(frame,
                       (int(pixel_x), int(pixel_y)),
                       10,
                       (0,255,0),
                       -1)
            cv2.imshow('Gesture Capture', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def __del__(self):
        """
        Clean up resources
        """
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    gc = GestureCapture()
    gc.traking_gestures()
    
    del gc
        
