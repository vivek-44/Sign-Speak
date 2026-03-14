import os
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

import cv2
import numpy as np
import mediapipe as mp
import time
from tensorflow.keras.models import load_model
from collections import deque, Counter
import tkinter.messagebox as tkMessageBox


class AlphabetDetector:
    def __init__(self, sequence_processor, mode="alphabet"):
        """
        mode = "alphabet" or "digit"
        """
        self.sequence_processor = sequence_processor
        self.sequence_processor.clear_sequence()
        self.mode = mode

        # ===============================
        # TEMPORAL STABILITY
        # ===============================
        self.buffer = deque(maxlen=15)
        self.vote_required = 8
        self.conf_threshold = 0.7
        self.cooldown = 1.3
        self.last_time = 0
        self.last_label = ""

        # ===============================
        # FPS
        # ===============================
        self.prev_time = time.time()
        self.fps = 0

        # ===============================
        # MEDIAPIPE
        # ===============================
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        # ===============================
        # LOAD MODELS
        # ===============================
        try:
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

            self.one_hand_model = load_model(
                "./models/alphabet_one_hand_model.h5", compile=False
            )
            self.two_hand_model = load_model(
                "./models/alphabet_two_hand_model.h5", compile=False
            )
            self.digit_model = load_model(
                "./models/digit_image_model.h5", compile=False
            )

            print("✅ Models loaded successfully")

        except Exception as e:
            tkMessageBox.showerror("Model Error", str(e))
            raise e

        # ⚠️ MUST MATCH TRAINING ORDER EXACTLY
        self.ONE_HAND_CLASSES = ['C','I','L','O','U','V']
        self.TWO_HAND_CLASSES = [
            'A','B','D','E','F','G','H','J','K',
            'M','N','P','Q','R','S','T','W','X','Y','Z'
        ]
        self.DIGITS = ['1','2','3','4','5','6']

    # ===============================
    # LANDMARK FLATTEN
    # ===============================
    def flatten_landmarks(self, hand):
        data = []
        for lm in hand.landmark:
            data.extend([lm.x, lm.y, lm.z])
        return data

    # ===============================
    # TEMPORAL CONFIRM
    # ===============================
    def confirm(self, label):
        self.buffer.append(label)
        common, count = Counter(self.buffer).most_common(1)[0]
        now = time.time()

        if count >= self.vote_required and now - self.last_time > self.cooldown:
            self.sequence_processor.add_to_sequence(common)
            self.last_label = common
            self.last_time = now
            self.buffer.clear()

        return self.last_label

    # ===============================
    # FPS UPDATE
    # ===============================
    def update_fps(self):
        now = time.time()
        self.fps = int(1 / (now - self.prev_time))
        self.prev_time = now

    # ===============================
    # FRAME PREDICTION
    # ===============================
    def predict_frame(self, frame):
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if not result.multi_hand_landmarks:
            return self.last_label, 0.0, frame

        hands = result.multi_hand_landmarks
        hand_count = len(hands)

        # ===============================
        # GREEN BOUNDING BOX (ALL HANDS)
        # ===============================
        xs, ys = [], []
        for hand in hands:
            for lm in hand.landmark:
                xs.append(int(lm.x * w))
                ys.append(int(lm.y * h))

        x1, y1 = max(0, min(xs)), max(0, min(ys))
        x2, y2 = min(w, max(xs)), min(h, max(ys))
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # ===============================
        # DIGIT MODE (ONLY DIGITS)
        # ===============================
        if self.mode == "digit":
            crop = frame[y1:y2, x1:x2]
            if crop.size > 0:
                img = cv2.resize(crop, (64, 64))
                img = img.astype("float32") / 255.0
                img = np.expand_dims(img, axis=0)

                preds = self.digit_model.predict(img, verbose=0)[0]
                idx = int(np.argmax(preds))
                conf = float(preds[idx])

                if conf > 0.85:
                    label = self.DIGITS[idx]
                    return self.confirm(label), conf, frame

            return self.last_label, 0.0, frame

        # ===============================
        # ALPHABET MODE
        # ===============================
        landmarks = [[0]*63, [0]*63]
        for i, hand in enumerate(hands[:2]):
            landmarks[i] = self.flatten_landmarks(hand)

        X = np.array(landmarks).flatten().reshape(1, -1)

        # ---- TWO HAND ALPHABET ----
        if hand_count == 2:
            preds = self.two_hand_model.predict(X, verbose=0)[0]
            idx = int(np.argmax(preds))
            conf = float(preds[idx])

            if conf > self.conf_threshold:
                label = self.TWO_HAND_CLASSES[idx]
                return self.confirm(label), conf, frame

        # ---- ONE HAND ALPHABET ----
        if hand_count == 1:
            preds = self.one_hand_model.predict(X, verbose=0)[0]
            idx = int(np.argmax(preds))
            conf = float(preds[idx])

            if conf > self.conf_threshold:
                label = self.ONE_HAND_CLASSES[idx]
                return self.confirm(label), conf, frame

        return self.last_label, 0.0, frame

    # ===============================
    # MAIN LOOP
    # ===============================
    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(1)

        if not cap.isOpened():
            tkMessageBox.showerror("Camera Error", "Camera not accessible")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            self.update_fps()

            label, conf, frame = self.predict_frame(frame)

            # LABEL
            if label:
                cv2.putText(
                    frame, f"{label} ({conf:.2f})",
                    (20, 430),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.1, (0,255,0), 3
                )

            # FPS
            cv2.putText(
                frame, f"FPS: {self.fps}",
                (520, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0,255,255), 2
            )

            # SEQUENCE
            cv2.putText(
                frame, f"Sequence: {self.sequence_processor.get_sequence()}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (255,0,0), 2
            )

            cv2.imshow("Sign Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.sequence_processor.clear_sequence()
                self.last_label = ""

        cap.release()
        cv2.destroyAllWindows()
