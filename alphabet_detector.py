
'''
import cv2
import numpy as np
import mediapipe as mp
#from keras.models import load_model
from tensorflow.keras.models import load_model
import os
import time
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageDraw, ImageFont

class AlphabetDetector:
    def __init__(self, sequence_processor, settings):
        self.sequence_processor = sequence_processor
        self.settings = settings
        
        # Clear sequence when starting a new detection session
        self.sequence_processor.clear_sequence()
        
        # Load Mediapipe hand detection model
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # Define image size
        self.img_width, self.img_height = 64, 64
        
        # Define class labels
        self.class_labels = [
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I", 
            "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
        ]
        
        # Load the trained model
        try:
            # Explicitly force CPU usage to avoid CUDA errors
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
            # Also set TensorFlow to use CPU
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
            import tensorflow as tf
            tf.config.set_visible_devices([], 'GPU')  # Disable GPU devices
            
            print("Loading model using CPU only...")
            self.model = load_model("./models/m.h5")
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
            tkMessageBox.showerror("Error", "Failed to load the sign language model. The application may not work correctly.")
    
    def run(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                tkMessageBox.showerror("Error", "Could not open webcam")
                return
    
            # Set optimal resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
            last_prediction_time = 0
            prediction_cooldown = 1.0  # Time between adding predictions to sequence
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Flip image for a mirrored effect
                frame = cv2.flip(frame, 1)
                
                # Convert frame to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process frame with Mediapipe
                result = self.hands.process(rgb_frame)
                
                hand_boxes = []
                if result.multi_hand_landmarks:
                    for hand_landmarks in result.multi_hand_landmarks:
                        # Get bounding box of hand
                        h, w, c = frame.shape
                        x_min = min([lm.x for lm in hand_landmarks.landmark]) * w
                        x_max = max([lm.x for lm in hand_landmarks.landmark]) * w
                        y_min = min([lm.y for lm in hand_landmarks.landmark]) * h
                        y_max = max([lm.y for lm in hand_landmarks.landmark]) * h
                        
                        # Increase bounding box size
                        padding = 20  # Adjust padding size as needed
                        x_min = max(0, int(x_min - padding))
                        x_max = min(w, int(x_max + padding))
                        y_min = max(0, int(y_min - padding))
                        y_max = min(h, int(y_max + padding))
                        
                        hand_boxes.append((x_min, y_min, x_max, y_max))
                
                # Merge bounding boxes if hands are touching
                if len(hand_boxes) > 1:
                    x_min = min(box[0] for box in hand_boxes)
                    y_min = min(box[1] for box in hand_boxes)
                    x_max = max(box[2] for box in hand_boxes)
                    y_max = max(box[3] for box in hand_boxes)
                elif len(hand_boxes) == 1:
                    x_min, y_min, x_max, y_max = hand_boxes[0]
                else:
                    x_min, y_min, x_max, y_max = None, None, None, None
                
                current_time = time.time()
                if x_min is not None:
                    # Draw bounding box
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    
                    # Extract and preprocess hand region
                    hand_img = frame[y_min:y_max, x_min:x_max]
                    if hand_img.size > 0:
                        hand_img = cv2.resize(hand_img, (self.img_width, self.img_height))
                        hand_img = np.expand_dims(hand_img, axis=0)  # Add batch dimension
                        hand_img = hand_img.astype('float32') / 255.0  # Normalize
                        
                        # Predict sign language
                        predictions = self.model.predict(hand_img, verbose=0)
                        predicted_class = np.argmax(predictions)
                        
                        # Display prediction on frame
                        predicted_text = self.class_labels[predicted_class]
                        cv2.putText(frame, f'Predicted: {predicted_text}', (x_min, y_min - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
                        # Add to sequence if enough time has passed
                        if current_time - last_prediction_time >= prediction_cooldown:
                            self.sequence_processor.add_to_sequence(predicted_text)
                            last_prediction_time = current_time
                
                # Display sequence at the top of the frame
                sequence_text = self.sequence_processor.get_sequence()
                cv2.putText(frame, f'Sequence: {sequence_text}', (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # Display translated text if available
                translated_text = self.sequence_processor.get_translated_text()
                if translated_text:
                    y_pos = 60
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
                
                # Display output
                cv2.imshow('Hand Sign Detection', frame)
                
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

    def put_multilingual_text(self, img, text, org, font_size, color):
        """Draw multilingual text on OpenCV image"""
        font_size_factor = 32  # Convert OpenCV font size to PIL font size
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        try:
            # Try using a system font that supports multilingual text
            font_path = None
            if os.path.exists("C:/Windows/Fonts/Arial.ttf"):  # Windows
                font_path = "C:/Windows/Fonts/Arial.ttf"
            elif os.path.exists("/usr/share/fonts/truetype/freefont/FreeMono.ttf"):  # Linux
                font_path = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
            elif os.path.exists("/System/Library/Fonts/AppleSDGothicNeo.ttc"):  # macOS
                font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
            
            if font_path:
                font = ImageFont.truetype(font_path, int(font_size * font_size_factor))
            else:
                font = ImageFont.load_default()
            
            draw.text(org, text, font=font, fill=color[::-1])  # Note: PIL uses RGB, OpenCV uses BGR
            result_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return result_img
        except Exception as e:
            print(f"Error rendering multilingual text: {e}")
            # Fall back to standard cv2.putText if PIL method fails
            cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_size, color, 2)
            return img 
'''
import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
import os
import time
import tkinter.messagebox as tkMessageBox
from collections import deque, Counter


class AlphabetDetector:

    def __init__(self, sequence_processor):
        self.sequence_processor = sequence_processor
        self.sequence_processor.clear_sequence()

        # =======================
        # STABILITY CONFIG
        # =======================
        self.pred_buffer = deque(maxlen=15)
        self.vote_required = 7
        self.confidence_threshold = 0.6
        self.prediction_cooldown = 1.5
        self._last_confirm_time = 0.0
        self.last_stable_label = ""

        # =======================
        # MEDIAPIPE
        # =======================
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        # =======================
        # MODEL
        # =======================
        self.img_width, self.img_height = 64, 64
        self.class_labels = [
            "1","2","3","4","5","6","7","8","9",
            "A","B","C","D","E","F","G","H","I",
            "J","K","L","M","N","O","P","Q","R",
            "S","T","U","V","W","X","Y","Z"
        ]

        try:
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
            import tensorflow as tf
            tf.config.set_visible_devices([], 'GPU')

            print("Loading alphabet model...")
            self.model = load_model("./models/ISLResNet50V2.h5", compile=False)
            print("Model loaded successfully")

        except Exception as e:
            self.model = None
            tkMessageBox.showerror("Error", f"Model loading failed:\n{e}")

    # =======================
    # PREPROCESS (MATCH TRAINING)
    # =======================
    def _preprocess_hand(self, hand_img):
        # Convert BGR → RGB
        img = cv2.cvtColor(hand_img, cv2.COLOR_BGR2RGB)

        # Resize to training size
        img = cv2.resize(img, (self.img_width, self.img_height))

        # Normalize
        img = img.astype("float32") / 255.0
        img = np.expand_dims(img, axis=0)
        return img

    # =======================
    # FRAME PREDICTION
    # =======================
    def predict_frame(self, frame):
        if self.model is None:
            return self.last_stable_label, 0.0

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if not result.multi_hand_landmarks:
            return self.last_stable_label, 0.0

        h, w, _ = frame.shape
        boxes = []

        # ---------- TIGHT HAND BOX FROM LANDMARKS ----------
        for hand in result.multi_hand_landmarks:
            xs = [int(lm.x * w) for lm in hand.landmark]
            ys = [int(lm.y * h) for lm in hand.landmark]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            # Adaptive padding (15% of hand size)
            pad = int(0.15 * max(x_max - x_min, y_max - y_min))

            x1 = max(0, x_min - pad)
            y1 = max(0, y_min - pad)
            x2 = min(w, x_max + pad)
            y2 = min(h, y_max + pad)

            boxes.append((x1, y1, x2, y2))

        # Select largest hand
        x1, y1, x2, y2 = max(boxes, key=lambda b: (b[2]-b[0])*(b[3]-b[1]))

        # ---------- SQUARE + CENTERED CROP ----------
        bw, bh = x2 - x1, y2 - y1
        size = max(bw, bh)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        sx1 = max(0, cx - size // 2)
        sy1 = max(0, cy - size // 2)
        sx2 = min(w, cx + size // 2)
        sy2 = min(h, cy + size // 2)

        hand_img = frame[sy1:sy2, sx1:sx2]
        if hand_img.size == 0:
            return self.last_stable_label, 0.0

        # Optional: slight blur to suppress background noise
        hand_img = cv2.GaussianBlur(hand_img, (3, 3), 0)

        # ---------- CNN PREDICTION ----------
        inp = self._preprocess_hand(hand_img)
        preds = self.model.predict(inp, verbose=0)[0]

        idx = int(np.argmax(preds))
        label = self.class_labels[idx]
        conf = float(preds[idx])

        if conf < self.confidence_threshold:
            return self.last_stable_label, conf

        # ---------- TEMPORAL SMOOTHING ----------
        self.pred_buffer.append((label, conf))
        labels = [l for l, _ in self.pred_buffer]
        best, count = Counter(labels).most_common(1)[0]
        avg_conf = np.mean([c for l, c in self.pred_buffer if l == best])

        now = time.time()
        if (
            count >= self.vote_required and
            avg_conf >= self.confidence_threshold and
            now - self._last_confirm_time >= self.prediction_cooldown
        ):
            self.sequence_processor.add_to_sequence(best)
            self.last_stable_label = best
            self._last_confirm_time = now
            self.pred_buffer.clear()

        return self.last_stable_label, conf

    # =======================
    # MAIN LOOP
    # =======================
    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            tkMessageBox.showerror("Error", "Webcam not found")
            return

        cap.set(3, 640)
        cap.set(4, 480)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            label, conf = self.predict_frame(frame)

            if label:
                cv2.putText(
                    frame,
                    f"{label} ({conf:.2f})",
                    (20, 440),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    3
                )

            seq = self.sequence_processor.get_sequence()
            cv2.putText(
                frame,
                f"Sequence: {seq}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 0, 0),
                2
            )

            cv2.imshow("Alphabet Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.sequence_processor.clear_sequence()
                self.last_stable_label = ""

        cap.release()
        cv2.destroyAllWindows()


