from ultralytics import YOLO
import os
import matplotlib.pyplot as plt
from datetime import datetime

def create_training_plots(results):
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    epochs = range(1, len(results.results_dict['metrics/precision(B)']) + 1)

    ax1.plot(epochs, results.results_dict['metrics/precision(B)'], label='Precision')
    ax1.plot(epochs, results.results_dict['metrics/recall(B)'], label='Recall')
    ax1.set_title('Precision & Recall')
    ax1.legend()

    ax2.plot(epochs, results.results_dict['metrics/mAP50(B)'])
    ax2.set_title('mAP50')

    ax3.plot(epochs, results.results_dict['train/box_loss'])
    ax3.set_title('Box Loss')

    ax4.plot(epochs, results.results_dict['train/cls_loss'])
    ax4.set_title('Class Loss')

    plt.tight_layout()
    plt.show()

def train_yolo_detector():
    model = YOLO('yolov8m.pt')

    training_params = {
        'task': 'detect',
        'data': './datam/data.yaml',
        'epochs': 25,
        'imgsz': 640,          # 🔴 increased for hand detail
        'plots': True,
        'save': True,
        'cache': 'disk',
        'device': 'cpu',
        'workers': 4,          # 🔴 safer for CPU
        'project': 'yolo_training',
        'name': f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'exist_ok': True,
        'pretrained': True,
        'optimizer': 'auto',
        'patience': 5,         # 🔴 early stopping
        'verbose': True,
        'seed': 42,
        'deterministic': True
    }

    print("\nStarting YOLOv8 Training\n")
    results = model.train(**training_params)
    print("\nTraining Completed\n")

    create_training_plots(results)
    return results, model

if __name__ == "__main__":
    results, trained_model = train_yolo_detector()
    print("Best model saved automatically by YOLOv8 (best.pt)")
