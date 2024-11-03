import cv2
import mediapipe as mp
import numpy as np
import os
import json
from datetime import datetime
import tensorflow as tf


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
            min_tracking_confidence=0.5,
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

    def load_model(self, model_path):
        """
        Load the trained model and class names

        Args:
            model_path (str): Path to the trained model (without extension)
        """
        try:
            self.model = tf.keras.models.load_model(f"{model_path}.keras")
            self.class_names = np.load(f"{model_path}_classes.npy")
            print(
                f"Loaded model with {len(self.class_names)} gesture classes: {self.class_names}"
            )
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
        Process a frame to detect hands and extract hand landmarks.
        Crops the frame to hand region and resizes to image_size.
        
        Args:
            frame (numpy.ndarray): Input frame
            
        Returns:
            tuple: Processed frame (cropped and resized empty frame with landmarks),
                hand landmarks data, and model-ready data
        """
        processed_frame = self.preprocess_frame(frame)
        results = self.hands.process(processed_frame)
        
        # Create an empty black frame with same dimensions as input frame
        empty_frame = np.zeros_like(frame)
        
        hand_data = []
        model_ready_data = None
        
        if results.multi_hand_landmarks:
            # Find bounding box for all hands
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on empty frame
                self.mp_draw.draw_landmarks(
                    empty_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                    connection_drawing_spec=self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)
                )
                
                # Update bounding box coordinates
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                
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
            
            # Add padding to bounding box
            padding = 20
            min_x = max(0, min_x - padding)
            min_y = max(0, min_y - padding)
            max_x = min(frame.shape[1], max_x + padding)
            max_y = min(frame.shape[0], max_y + padding)
            
            # Ensure box is square by taking max dimension
            width = max_x - min_x
            height = max_y - min_y
            size = max(width, height)
            
            # Adjust box to be square while keeping hands centered
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            min_x = max(0, center_x - size // 2)
            min_y = max(0, center_y - size // 2)
            max_x = min(frame.shape[1], min_x + size)
            max_y = min(frame.shape[0], min_y + size)
            
            # Crop the frame to the hand region
            empty_frame = empty_frame[int(min_y):int(max_y), int(min_x):int(max_x)]
            
            # Resize to image_size
            empty_frame = cv2.resize(empty_frame, (self.image_size[0], self.image_size[1]))
        
        return empty_frame, hand_data, model_ready_data

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
        with open(data_path, "w") as f:
            json.dump(hand_data, f)

    def check_for_existing(self, gesture_name):
        """
        Check if a gesture already exists

        Args:
            gesture_name (str): Name of the gesture
        """
        gesture_dir = os.path.join(self.base_dir, gesture_name)
        if os.path.exists(gesture_dir):
            print(f"Gesture '{gesture_name}' already exists. Overwrite? (y/n)")
            choice = input()
            if choice.lower() == "y":
                for f in os.listdir(gesture_dir):
                    os.remove(os.path.join(gesture_dir, f))
                os.rmdir(gesture_dir)
                print(f"Deleted existing gesture: {gesture_name}")

    def capture_gesture(self, gesture_name, num_frames=100):
        """
        Capture frames for a specific gesture

        Args:
            gesture_name (str): Name of the gesture to capture
            num_frames (int): Number of frames to capture
        """
        self.check_for_existing(gesture_name)

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
                    0.5,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow("Gesture Capture", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
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
                        2,
                    )

            cv2.imshow("Gesture Recognition", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    def __del__(self):
        """
        Clean up resources
        """
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    while True:
        mode = input("Choose mode (cap/pred): ")
        if mode == "cap":
            gc = GestureCapture(image_size=(128, 128))
            gesture_name = input("Enter gesture name: ")
            frames = int(input("Enter number of frames to capture: "))
            gc.capture_gesture(gesture_name, frames)
        elif mode == "pred":
            gc = GestureCapture(image_size=(128, 128), model_path="gesture_model")
            gc.run_prediction()

        if gc is not None:
            del gc
            gc = None
        else:
            break
