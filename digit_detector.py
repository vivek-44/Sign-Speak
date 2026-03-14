# digit_detector.py
import os
import time
import cv2
import numpy as np
import mediapipe as mp
from collections import deque, Counter
from tensorflow.keras.models import load_model
import tkinter.messagebox as tkMessageBox

# 🔴 Windows OpenCV fix
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"


class DigitDetector:
    def __init__(self, sequence_processor):
        self.sequence_processor = sequence_processor
        self.sequence_processor.clear_sequence()

        # ===============================
        # STABILITY CONFIG
        # ===============================
        self.buffer = deque(maxlen=10)
        self.vote_required = 6
        self.conf_threshold = 0.75
        self.cooldown = 1.0
        self.last_time = 0.0
        self.last_label = ""

        # ===============================
        # DIGIT CLASSES
        # ===============================
        self.CLASSES = ['1','2','3','4','5','6','7','8','9']

        # ===============================
        # MEDIAPIPE (ONE HAND ONLY)
        # ===============================
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        # ===============================
        # LOAD IMAGE CNN MODEL
        # ===============================
        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

            self.model = load_model(
                "./models/digit_image_model.h5",
                compile=False
            )

            print("✅ Digit image CNN loaded")

        except Exception as e:
            tkMessageBox.showerror("Model Error", str(e))
            raise e

        # ===============================
        # FPS
        # ===============================
        self.prev_time = time.time()
        self.fps = 0.0

    # ==================================================
    # TEMPORAL CONFIRMATION
    # ==================================================
    def confirm(self, label):
        self.buffer.append(label)
        common, count = Counter(self.buffer).most_common(1)[0]
        now = time.time()

        if count >= self.vote_required and (now - self.last_time) > self.cooldown:
            self.sequence_processor.add_to_sequence(common)
            self.last_label = common
            self.last_time = now
            self.buffer.clear()

        return self.last_label

    # ==================================================
    # FRAME PREDICTION
    # ==================================================
    def predict_frame(self, frame):
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if not result.multi_hand_landmarks:
            return self.last_label, 0.0, frame

        hand = result.multi_hand_landmarks[0]

        # -------------------------------
        # GREEN BOX
        # -------------------------------
        xs = [int(lm.x * w) for lm in hand.landmark]
        ys = [int(lm.y * h) for lm in hand.landmark]
        x1, y1 = max(0, min(xs)), max(0, min(ys))
        x2, y2 = min(w, max(xs)), min(h, max(ys))

        pad = int(0.2 * max(x2 - x1, y2 - y1))
        x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
        x2, y2 = min(w, x2 + pad), min(h, y2 + pad)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # -------------------------------
        # IMAGE CNN PREDICTION
        # -------------------------------
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return self.last_label, 0.0, frame

        img = cv2.resize(crop, (64, 64))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype("float32") / 255.0
        img = np.expand_dims(img, axis=0)

        preds = self.model.predict(img, verbose=0)[0]
        idx = int(np.argmax(preds))
        conf = float(preds[idx])

        if conf >= self.conf_threshold:
            label = self.confirm(self.CLASSES[idx])
        else:
            label = self.last_label

        return label, conf, frame

    # ==================================================
    # MAIN LOOP
    # ==================================================
    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(1.0)

        if not cap.isOpened():
            tkMessageBox.showerror("Camera Error", "Camera not accessible")
            return

        cap.set(3, 640)
        cap.set(4, 480)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            label, conf, frame = self.predict_frame(frame)

            # FPS
            now = time.time()
            self.fps = 1.0 / (now - self.prev_time)
            self.prev_time = now

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

            cv2.putText(
                frame,
                f"FPS: {self.fps:.1f}",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 0, 0),
                2
            )

            cv2.imshow("Digit Detection (1–9)", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.sequence_processor.clear_sequence()
                self.last_label = ""

        cap.release()
        cv2.destroyAllWindows()
