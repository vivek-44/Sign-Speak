# Indian Sign Language Recognition

## Overview
This project aims to recognize Indian Sign Language (ISL) gestures using deep learning and computer vision techniques. The system detects hand signs in real-time and converts them into text and speech outputs, enabling effective communication for the hearing and speech impaired.

## Features
- **Real-time sign detection** using ResNet50V2, MediaPipe Hands, and YOLOv8.
- **Text-to-speech conversion** for recognized signs.
- **Multi-language support** for wider accessibility.
- **GUI interface** built with Tkinter and OpenCV.
- **Dataset preprocessing and augmentation** for improved model performance.

## Technologies Used
- **Deep Learning Models**: ResNet50V2, YOLOv8  
- **Hand Tracking**: MediaPipe Hands  
- **Frameworks & Libraries**: TensorFlow, Keras, OpenCV, NumPy, Tkinter  
- **Programming Language**: Python  

## Installation

1. **Clone the repository:**
   ```sh
   https://github.com/Basant678/SignSpeak.git
   cd ISLTOSPEECH
   ```

2. Create and activate a virtual environment
   ```sh
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

## Installation
   ```sh
3. Install dependencies:
   pip install -r requirements.txt
   ```

## Usage
1. Run the real-time sign language recognition system:
   ```sh
   python main.py
   ```
2. The GUI will open, allowing users to sign gestures and see text and speech output.

## Dataset
- The dataset consists of **35 classes** of Indian Sign Language gestures.
- Data is preprocessed and augmented to improve model generalization.

## Model Training
- The model is trained using **categorical crossentropy loss** and the **Adam optimizer**.
- Training parameters:
  - **Epochs**: 10
  - **Learning Rate**: 0.0001
  - **Optimizer**: Adam

## Architecture Diagram
- The system consists of:
  - **Input**: Live video feed
  - **Preprocessing**: Hand detection and segmentation using MediaPipe & YOLOv8
  - **Model**: ResNet50V2 for classification
  - **Conversion**: Predicted text converted to speech
  - **Output**: Displayed text and audio feedback

## Future Enhancements
- Increase dataset size and diversity.
- Improve model accuracy with more advanced architectures.
- web-based applications.


