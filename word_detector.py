'''

import cv2
import numpy as np
import time
import os
import tkinter.messagebox as tkMessageBox
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont

class WordDetector:
    def __init__(self, sequence_processor, settings):
        self.sequence_processor = sequence_processor
        self.settings = settings
        
        # Clear sequence when starting a new detection session
        self.sequence_processor.clear_sequence()
        
        # Set environment variables to handle GPU issues
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU usage
        
        # Class names
        self.CLASS_NAMES = ['I', 'apple', 'can', 'get', 'good', 'have', 'help', 'how', 'like', 
                            'love', 'my', 'no', 'sorry', 'thank-you', 'want', 'yes', 'you', 'your']
    
    def load_model(self, model_path):
        """Load the YOLOv8 model"""
        print(f"Loading model from {model_path}...")
        try:
            # Try to configure YOLO to use CPU only
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
            model = YOLO(model_path)
            print("Model loaded successfully!")
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            # If the first attempt failed, try with more aggressive settings
            try:
                print("Retrying with alternative settings...")
                # Force CPU usage with YOLO-specific settings
                model = YOLO(model_path, task='detect', device='cpu')
                print("Model loaded successfully with CPU!")
                return model
            except Exception as e2:
                print(f"Second attempt failed: {e2}")
                return None
            
    def draw_detection_info(self, frame, results, fps):
        """Draw detection results and FPS on the frame"""
        # Draw FPS
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 255, 0), 2)
        
        # If no detections, show message
        if len(results) == 0 or len(results[0].boxes) == 0:
            cv2.putText(frame, "No sign detected", (frame.shape[1]//2 - 100, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return frame
        
        # Process results (only the first image's results)
        boxes = results[0].boxes
        
        for i, box in enumerate(boxes):
            # Get box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Get confidence and class
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.CLASS_NAMES[class_id]
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label background
            label = f"{class_name}: {confidence:.2f}"
            (label_width, label_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(frame, (x1, y1 - 20), (x1 + label_width, y1), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (0, 0, 0), 1)
        
        return frame
        
    def run(self):
        try:
            model_path = "./models/best.pt"
            model = self.load_model(model_path)
            if model is None:
                tkMessageBox.showerror("Error", "Failed to load YOLO model")
                return
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                tkMessageBox.showerror("Error", "Could not open webcam")
                return
            
            # Set optimal resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            frame_count = 0
            start_time = time.time()
            fps = 0
            skip_frames = 2  # Process every 3rd frame
            last_prediction_time = 0
            prediction_cooldown = 1.0  # Time between adding predictions to sequence
    
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
    
                frame_count += 1
                if frame_count % skip_frames != 0:  # Skip frames
                    continue
                
                try:
                    frame = cv2.flip(frame, 1)
                    
                    # Calculate FPS
                    if frame_count % 30 == 0:
                        fps = 30 / (time.time() - start_time)
                        start_time = time.time()
                    
                    # Optimize YOLO inference
                    results = model.predict(
                        frame,
                        conf=0.4,
                        iou=0.45,
                        max_det=5,  # Limit detections
                        verbose=False
                    )
                    
                    frame = self.draw_detection_info(frame, results, fps)
                    
                    # Display sequence at the top of the frame
                    sequence_text = self.sequence_processor.get_sequence()
                    cv2.putText(frame, f'Sequence: {sequence_text}', (20, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    # Display translated text if available
                    translated_text = self.sequence_processor.get_translated_text()
                    if translated_text:
                        y_pos = 110
                        # Choose a smaller font size for non-Latin scripts
                        font_size = 0.6
                        if self.settings['language'] != 'en':
                            # For non-Latin scripts, use a PIL-based text rendering approach
                            # Convert OpenCV image to PIL format
                            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            # Create a drawing context
                            draw = ImageDraw.Draw(pil_img)
                            
                            # Try to use a font that supports the language
                            try:
                                # Check if we can access system fonts
                                font_path = None
                                # Common font paths for different systems
                                possible_fonts = [
                                    "arial.ttf",  # Windows
                                    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",  # Linux
                                    "/System/Library/Fonts/Arial Unicode.ttf"  # macOS
                                ]
                                
                                for font in possible_fonts:
                                    if os.path.exists(font):
                                        font_path = font
                                        break
                                
                                if font_path:
                                    font = ImageFont.truetype(font_path, 20)  # Size 20
                                else:
                                    font = ImageFont.load_default()
                                    
                                # Split long translations into multiple lines
                                for i in range(0, len(translated_text), 50):
                                    line = translated_text[i:i+50]
                                    draw.text((20, y_pos), line, font=font, fill=(0, 0, 255))
                                    y_pos += 30
                                    
                                # Convert back to OpenCV format
                                frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                                
                            except Exception as e:
                                print(f"Error rendering text: {e}")
                                # Fallback to default method
                                for i in range(0, len(translated_text), 50):
                                    line = translated_text[i:i+50]
                                    cv2.putText(frame, line, (20, y_pos),
                                                cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 255), 2)
                                    y_pos += 30
                        else:
                            # For English, use the standard OpenCV text rendering
                            for i in range(0, len(translated_text), 50):
                                line = translated_text[i:i+50]
                                cv2.putText(frame, line, (20, y_pos),
                                            cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 255), 2)
                                y_pos += 30
                    
                    cv2.imshow("ISL Word Detection", frame)
                    
                    # Process audio feedback and add to sequence less frequently
                    current_time = time.time()
                    if (frame_count % (skip_frames * 5) == 0 and len(results) > 0 
                            and len(results[0].boxes) > 0 and current_time - last_prediction_time >= prediction_cooldown):
                        box = results[0].boxes[0]
                        class_id = int(box.cls[0])
                        detected_text = self.CLASS_NAMES[class_id]
                        self.sequence_processor.add_to_sequence(detected_text)
                        last_prediction_time = current_time
                    
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    continue
    
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    # Clear sequence with 'c' key
                    self.sequence_processor.clear_sequence()
                elif key == ord('s'):
                    # Speak sequence with 's' key
                    self.sequence_processor.speak_sequence()
            
        except Exception as e:
            tkMessageBox.showerror("Error", f"An error occurred: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows() 
'''

# word_detector.py

import cv2
import time
import os
import tkinter.messagebox as tkMessageBox
from ultralytics import YOLO


class WordDetector:
    def __init__(self, sequence_processor):
        self.sequence_processor = sequence_processor
        self.sequence_processor.clear_sequence()

        # Force CPU usage
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

        # Class names (MUST match YOLO training order)
        self.CLASS_NAMES = [
            'I', 'apple', 'can', 'get', 'good', 'have', 'help', 'how', 'like',
            'love', 'my', 'no', 'sorry', 'thank-you', 'want', 'yes', 'you', 'your'
        ]

        self.prediction_cooldown = 1.5
        self.last_prediction_time = 0.0
        self.confidence_threshold = 0.7

    def load_model(self, model_path):
        try:
            print(f"Loading YOLO model: {model_path}")
            return YOLO(model_path)
        except Exception as e:
            tkMessageBox.showerror("Error", f"Model load failed:\n{e}")
            return None

    def run(self):
        try:
            model = self.load_model("./models/best.pt")
            if model is None:
                return

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                tkMessageBox.showerror("Error", "Could not open webcam")
                return

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            fps, frame_count = 0, 0
            start_time = time.time()

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                frame_count += 1

                # FPS calculation
                if frame_count % 30 == 0:
                    fps = 30 / (time.time() - start_time)
                    start_time = time.time()

                # YOLO inference
                results = model.predict(
                    frame,
                    conf=self.confidence_threshold,
                    iou=0.45,
                    max_det=3,
                    verbose=False
                )

                # Draw FPS
                cv2.putText(
                    frame, f"FPS: {fps:.1f}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2
                )

                if results and results[0].boxes:
                    # Choose highest confidence detection
                    best_box = max(
                        results[0].boxes,
                        key=lambda b: float(b.conf[0])
                    )

                    confidence = float(best_box.conf[0])
                    class_id = int(best_box.cls[0])
                    word = self.CLASS_NAMES[class_id]

                    x1, y1, x2, y2 = map(int, best_box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    label = f"{word}: {confidence:.2f}"
                    cv2.putText(
                        frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
                    )

                    # Add to sequence with cooldown
                    current_time = time.time()
                    if (
                        confidence >= self.confidence_threshold and
                        current_time - self.last_prediction_time >= self.prediction_cooldown
                    ):
                        self.sequence_processor.add_to_sequence(word)
                        self.last_prediction_time = current_time

                # Show sequence
                seq = self.sequence_processor.get_sequence()
                cv2.putText(
                    frame, f"Sequence: {seq}",
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2
                )

                cv2.imshow("ISL Word Detection", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    self.sequence_processor.clear_sequence()

        except Exception as e:
            tkMessageBox.showerror("Error", str(e))
        finally:
            cap.release()
            cv2.destroyAllWindows()
