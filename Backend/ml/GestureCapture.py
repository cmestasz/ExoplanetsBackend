from typing import Any, Dict
import cv2
import mediapipe as mp
import numpy as np
import os
import json
from datetime import datetime
import tensorflow as tf
import statistics
import time

class GestureCapture:
    def __init__(self, model_path=None, camera_index=0, image_size=(128, 128)):
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
        
        # Initialize camera
        self.cap = cv2.VideoCapture(camera_index)
        
        # Create base directory for storing gestures
        self.base_dir = "gestures"
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        
        # Load model and class names if provided
        self.model = None
        self.class_names = None
        if model_path:
            self.load_model(model_path)
            
    def draw_frame(self, frame, landmark):
        self.mp_draw.draw_landmarks(
            frame,
            landmark,
            self.mp_hands.HAND_CONNECTIONS
        )

    def load_model(self, model_path):
        """
        Load the trained model and class names
        
        Args:
            model_path (str): Path to the trained model (without extension)
        """
        try:
            self.model = tf.keras.models.load_model(f'{model_path}.keras')
            self.class_names = np.load(f'{model_path}_classes.npy')
            print(f"Loaded model with {len(self.class_names)} gesture classes: {self.class_names}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
            self.class_names = None
            
    def preprocess_frame(self, frame):
        """
        Preprocess the frame for better hand detection
        
        Args:
            frame (numpy.ndarray): Input frame from camera
            
        Returns:
            numpy.ndarray: Preprocessed frame
        """
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Basic preprocessing
        frame_rgb = cv2.GaussianBlur(frame_rgb, (5, 5), 0)
        frame_rgb = cv2.equalizeHist(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY))
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_GRAY2RGB)
        
        return frame_rgb

    def process_frame(self, frame):
        """
        Process a frame to detect hands and extract hand landmarks
        
        Args:
            frame (numpy.ndarray): Input frame
            
        Returns:
            tuple: Processed frame, hand landmarks data, and model-ready data
        """
        processed_frame = self.preprocess_frame(frame)
        results = self.hands.process(processed_frame)
        
        hand_data = []
        model_ready_data = None
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on frame
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )
                
                # Extract landmark positions
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z
                    })
                hand_data.append(landmarks)
                
                # Prepare data for model prediction
                if self.model and landmarks:
                    flat_landmarks = []
                    for lm in landmarks:
                        flat_landmarks.extend([lm['x'], lm['y'], lm['z']])
                    model_ready_data = np.array(flat_landmarks)
        
        return frame, hand_data, model_ready_data

    def send_gesture(self, gesture:Dict) ->None:
        if (not gesture): return
        json_str = json.dumps(gesture, indent=4)
        print(json_str)

    def is_click(self, hand_landmarks)-> bool:
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

        mean_thumb_x = statistics.mean([
            hand_landmarks[4].x,
            hand_landmarks[3].x,
            hand_landmarks[2].x,
        ])

        flag = alignment and \
            ( -0.07 < range_index_finger_x < 0.07 ) and \
            middle_hand_y < mean_finger_y and \
            hand_landmarks[4].x < hand_landmarks[3].x
            

        return flag


    def detect_gesture(self, hand_landmarks)-> str:
        if (self.is_click(hand_landmarks)): return "click"
        return "none"

        

    def traking_gestures(self) -> None:
        """
        Process each frame to detect hand's gestures
        
        """

        left_tracker: Dict[str, Any] = {
            'label': None,
            'desc': None,
        }

        right_tracker: str = 'none'
        counter_click: int = 0

        start_time = time.time()


        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            frame = cv2.flip(frame, 1)
            processed_frame = self.preprocess_frame(frame)
            results = self.hands.process(processed_frame)

            left_hand = None
            right_hand = None

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

                if (right_hand != None):
                    send['cursor'] = {
                        'x': right_hand['landmark'].landmark[8].x,
                        'y': right_hand['landmark'].landmark[8].y,
                    }
                    gesture = self.detect_gesture( right_hand['landmark'].landmark )
                    if (right_tracker == 'none'):
                        if (gesture == 'click'):
                            counter_click += 1
                            right_tracker = 'click'
                    elif (right_tracker == 'click'):
                        if (gesture == 'click'):
                            counter_click += 1
                            if (counter_click > 15):
                                right_tracker = 'prepare'
                        else: 
                            counter_click = 0
                            right_tracker = 'none'
                    elif (right_tracker == 'prepare'):
                        if (gesture == 'click'):
                            counter_click += 1
                            if (counter_click > 40):
                                right_tracker = 'select'
                                print('select')
                                send['right_gesture'] = 'select'
                        else: 
                            send['right_gesture'] = 'click'
                            print ('click')
                            right_tracker = 'none'
                            counter_click = 0
                    elif(right_tracker == 'select'):
                        if (not gesture == 'click'):
                            print('deselect')
                            send['right_gesture'] = 'deselect'
                            right_tracker = 'none'
                            counter_click = 0
                        
                #self.send_gesture(send)



            if (right_hand != None):
                if  self.detect_gesture(right_hand['landmark'].landmark) == 'Click':
                    print("============ de hecho ============")


            cv2.imshow('Gesture Capture', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                #hand_landmarks = results.multi_hand_landmarks
                #self.mp_draw.draw_landmarks(
                #    frame,
                #    hand_landmarks,
                #    self.mp_hands.HAND_CONNECTIONS
                #)

    def predict_gesture(self, frame, landmarks):
        """
        Predict gesture using the loaded model
        
        Args:
            frame (numpy.ndarray): Current frame
            landmarks (numpy.ndarray): Landmark data
            
        Returns:
            tuple: Predicted gesture name and confidence score
        """
        if self.model is None:
            return None, 0
            
        # Preprocess image for model
        img = cv2.resize(frame, self.image_size)
        img = img / 255.0
        img = np.expand_dims(img, axis=0)
        
        # Reshape landmarks
        landmarks = np.expand_dims(landmarks, axis=0)
        
        # Make prediction
        prediction = self.model.predict([img, landmarks], verbose=0)
        predicted_class = np.argmax(prediction[0])
        confidence = prediction[0][predicted_class]
        
        return self.class_names[predicted_class], confidence

    def save_gesture_frame(self, frame, hand_data, gesture_name):
        """
        Save the frame and associated hand data
        
        Args:
            frame (numpy.ndarray): Frame to save
            hand_data (list): List of hand landmarks
            gesture_name (str): Name of the gesture
        """
        gesture_dir = os.path.join(self.base_dir, gesture_name)
        if not os.path.exists(gesture_dir):
            os.makedirs(gesture_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        image_path = os.path.join(gesture_dir, f"{timestamp}.jpg")
        cv2.imwrite(image_path, frame)
        
        data_path = os.path.join(gesture_dir, f"{timestamp}.json")
        with open(data_path, 'w') as f:
            json.dump(hand_data, f)

    def capture_gesture(self, gesture_name, num_frames=100):
        """
        Capture frames for a specific gesture
        
        Args:
            gesture_name (str): Name of the gesture to capture
            num_frames (int): Number of frames to capture
        """
        frames_captured = 0
        
        while frames_captured < num_frames:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            frame, hand_data, _ = self.process_frame(frame)
            
            if hand_data and len(hand_data) == 2:
                self.save_gesture_frame(frame, hand_data, gesture_name)
                frames_captured += 1
                
                cv2.putText(
                    frame,
                    f"Capturing {gesture_name}: {frames_captured}/{num_frames}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
            
            cv2.imshow('Gesture Capture', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        print(f"Captured {frames_captured} frames for gesture: {gesture_name}")

    def run_prediction(self, confidence_threshold=0.7):
        """
        Run real-time prediction using the loaded model
        
        Args:
            confidence_threshold (float): Minimum confidence score to show prediction
        """
        if self.model is None:
            print("No model loaded. Please load a model first.")
            return
            
        print("Running real-time prediction. Press 'q' to quit.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Process frame and get predictions
            frame, hand_data, model_ready_data = self.process_frame(frame)
            
            if model_ready_data is not None:
                gesture_name, confidence = self.predict_gesture(frame, model_ready_data)
                
                if confidence >= confidence_threshold:
                    # Draw prediction on frame
                    cv2.putText(
                        frame,
                        f"{gesture_name}: {confidence:.2f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0) if confidence > 0.9 else (0, 255, 255),
                        2
                    )
            
            cv2.imshow('Gesture Recognition', frame)
            
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
    #mode = input("Choose mode (cap/pred): ")
    #if mode == 'cap':
    #    gc = GestureCapture()
    #    gesture_name = input("Enter gesture name: ")
    #    frames = int(input("Enter number of frames to capture: "))
    #    gc.capture_gesture(gesture_name, frames)
    #elif mode == 'pred':
    #    gc = GestureCapture(model_path="gesture_model")
    #    gc.run_prediction()
    
    del gc
        
