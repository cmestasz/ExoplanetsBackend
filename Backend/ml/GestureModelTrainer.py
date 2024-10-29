import os
import json
import numpy as np
from glob import glob
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import cv2
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.layers import (
    Input, Conv2D, MaxPooling2D, Dense, Dropout, 
    Flatten, concatenate, BatchNormalization
)

class GestureModelTrainer:
    def __init__(self, data_dir="gestures", image_size=(128, 128), frames_to_skip=20):
        """
        Initialize the GestureModelTrainer class
        
        Args:
            data_dir (str): Directory containing gesture data
            image_size (tuple): Size to resize images to
            frames_to_skip (int): Number of initial frames to skip for each gesture
        """
        self.data_dir = data_dir
        self.image_size = image_size
        self.frames_to_skip = frames_to_skip
        self.label_encoder = LabelEncoder()
        
    def load_data(self):
        """
        Load image and landmark data from the gestures directory, 
        skipping the first n frames of each gesture
        
        Returns:
            tuple: Arrays of images, landmarks, labels, and number of classes
        """
        images = []
        landmarks = []
        labels = []
        
        # Get all gesture folders
        gesture_folders = [f for f in os.listdir(self.data_dir) 
                         if os.path.isdir(os.path.join(self.data_dir, f))]
        
        for gesture in gesture_folders:
            gesture_path = os.path.join(self.data_dir, gesture)
            
            # Get all image files and sort them by timestamp
            image_files = glob(os.path.join(gesture_path, "*.jpg"))
            image_files.sort()  # Sort to ensure chronological order
            
            # Skip the first n frames
            image_files = image_files[self.frames_to_skip:]
            
            for img_path in image_files:
                # Load and preprocess image
                img = cv2.imread(img_path)
                if img is None:
                    continue
                    
                img = cv2.resize(img, self.image_size)
                img = img / 255.0  # Normalize
                
                # Get corresponding JSON file
                json_path = img_path.replace('.jpg', '.json')
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        try:
                            hand_data = json.load(f)
                            
                            # If hand data exists, flatten and pad/truncate to fixed size
                            if hand_data:
                                # Take first hand if multiple hands
                                first_hand = hand_data[0]
                                # Flatten the landmark coordinates
                                flat_landmarks = []
                                for landmark in first_hand:
                                    flat_landmarks.extend([
                                        landmark['x'], 
                                        landmark['y'], 
                                        landmark['z']
                                    ])
                                
                                images.append(img)
                                landmarks.append(flat_landmarks)
                                labels.append(gesture)
                        except json.JSONDecodeError:
                            print(f"Error reading JSON file: {json_path}")
                            continue
        
        if not images:
            raise ValueError("No valid data found after skipping initial frames!")
        
        # Convert to numpy arrays
        X_img = np.array(images)
        X_landmarks = np.array(landmarks)
        
        # Encode labels
        y = self.label_encoder.fit_transform(labels)
        num_classes = len(self.label_encoder.classes_)
        
        print(f"Loaded {len(images)} frames after skipping {self.frames_to_skip} initial frames per gesture")
        print(f"Found {num_classes} gesture classes: {self.label_encoder.classes_}")
        
        return X_img, X_landmarks, y, num_classes
    
    def build_model(self, num_classes):
        """
        Build a multi-modal neural network model
        
        Args:
            num_classes (int): Number of gesture classes
            
        Returns:
            tensorflow.keras.Model: Compiled model
        """
        # Image input branch
        img_input = Input(shape=(*self.image_size, 3))
        
        x = Conv2D(32, (3, 3), activation='relu')(img_input)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        
        x = Conv2D(64, (3, 3), activation='relu')(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        
        x = Conv2D(128, (3, 3), activation='relu')(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        
        x = Flatten()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.5)(x)
        img_features = Dense(256, activation='relu')(x)
        
        # Landmark input branch (63 values for 21 3D landmarks)
        landmark_input = Input(shape=(63,))
        
        y = Dense(128, activation='relu')(landmark_input)
        y = BatchNormalization()(y)
        y = Dense(64, activation='relu')(y)
        landmark_features = Dense(32, activation='relu')(y)
        
        # Combine both branches
        combined = concatenate([img_features, landmark_features])
        
        # Final classification layers
        z = Dense(128, activation='relu')(combined)
        z = Dropout(0.5)(z)
        output = Dense(num_classes, activation='softmax')(z)
        
        # Create model
        model = Model(
            inputs=[img_input, landmark_input],
            outputs=output
        )
        
        # Compile model
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, epochs=100, batch_size=32, validation_split=0.3):
        """
        Train the model
        
        Args:
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            validation_split (float): Fraction of data to use for validation
            
        Returns:
            tuple: Trained model and training history
        """
        print(f"Loading data (skipping first {self.frames_to_skip} frames per gesture)...")
        X_img, X_landmarks, y, num_classes = self.load_data()
        
        print(f"Total samples after filtering: {len(X_img)}")
        
        # Split data into train and validation sets
        (X_img_train, X_img_val, 
         X_landmarks_train, X_landmarks_val,
         y_train, y_val) = train_test_split(
            X_img, X_landmarks, y,
            test_size=validation_split,
            stratify=y,
            random_state=42
        )
        
        print(f"Training samples: {len(X_img_train)}")
        print(f"Validation samples: {len(X_img_val)}")
        
        # Build and train model
        model = self.build_model(num_classes)
        
        # Create callbacks
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.2,
            patience=5,
            min_lr=1e-6
        )
        
        # Train model
        history = model.fit(
            [X_img_train, X_landmarks_train],
            y_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_data=([X_img_val, X_landmarks_val], y_val),
            callbacks=[early_stopping, reduce_lr],
            verbose=1
        )
        
        # Evaluate final model
        final_loss, final_accuracy = model.evaluate(
            [X_img_val, X_landmarks_val],
            y_val,
            verbose=0
        )
        print(f"\nFinal validation accuracy: {final_accuracy:.4f}")
        
        return model, history
    
    def save_model(self, model, model_path='gesture_model'):
        """
        Save the trained model and label encoder
        
        Args:
            model: Trained Keras model
            model_path (str): Path to save the model
        """
        # Save model
        model.save(f'{model_path}.keras')
        
        # Save label encoder classes
        np.save(f'{model_path}_classes.npy', self.label_encoder.classes_)
        print(f"Model and classes saved to {model_path}")
        
    def predict_gesture(self, model, image, landmarks):
        """
        Predict gesture from image and landmarks
        
        Args:
            model: Trained Keras model
            image (numpy.ndarray): Image array
            landmarks (numpy.ndarray): Landmark array
            
        Returns:
            str: Predicted gesture name and confidence score
        """
        # Preprocess image
        img = cv2.resize(image, self.image_size)
        img = img / 255.0
        img = np.expand_dims(img, axis=0)
        
        # Reshape landmarks
        landmarks = np.expand_dims(landmarks, axis=0)
        
        # Make prediction
        prediction = model.predict([img, landmarks], verbose=0)
        predicted_class = np.argmax(prediction[0])
        confidence = prediction[0][predicted_class]
        
        gesture_name = self.label_encoder.inverse_transform([predicted_class])[0]
        return gesture_name, confidence
    
if __name__ == "__main__":
    trainer = GestureModelTrainer(frames_to_skip=50)
    model, history = trainer.train()
    trainer.save_model(model, 'gesture_model')