"""
from tkinter import *
from PIL import ImageTk, Image
import tkinter.messagebox as tkMessageBox
import ctypes
import os
import json
from tkinter import ttk
import threading
import time

# Import custom modules
from sequence_processor import SequenceProcessor
from alphabet_detector import AlphabetDetector
from word_detector import WordDetector

# Define supported languages
SUPPORTED_LANGUAGES = {
    'English': 'en',
    'Hindi': 'hi',
    'Tamil': 'ta',
    'Telugu': 'te',
    'Malayalam': 'ml',
    'Kannada': 'kn',
    'Bengali': 'bn',
    'Marathi': 'mr'
}

# Load settings from file or use defaults
try:
    with open('settings.json', 'r') as f:
        SETTINGS = json.load(f)
except:
    SETTINGS = {
        'language': 'en',
        'audio_enabled': True,
        'frame_delay': 15
    }

# Initialize sequence processor
sequence_processor = SequenceProcessor(SETTINGS)

# Setup main window
directory = "./"
home = Tk()
home.title("Sign To Text and Speech")
img = Image.open(directory+"/assets/home.jpeg")
img = ImageTk.PhotoImage(img)
panel = Label(home, image=img)
panel.pack(side="top", fill="both", expand="yes")
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
[w, h] = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]
lt = [w, h]
a = str(lt[0]//2-600)
b= str(lt[1]//2-360)
home.geometry("1200x720+"+a+"+"+b)
home.resizable(0,0)


def Exit():
    global home
    result = tkMessageBox.askquestion(
        "Sign To Text and Speech", 'Are you sure you want to exit?', icon="warning")
    if result == 'yes':
        home.destroy()
        exit()

def digitalpha():
    # Clear the sequence before starting a new detection
    sequence_processor.clear_sequence()
    detector = AlphabetDetector(sequence_processor, SETTINGS)
    detector.run()
    # After window is closed, speak the final sequence if needed
    if sequence_processor.sequence and SETTINGS['audio_enabled']:
        threading.Thread(target=sequence_processor.speak_final_sequence, daemon=True).start()
    
def yolo():
    # Clear the sequence before starting a new detection
    sequence_processor.clear_sequence()
    detector = WordDetector(sequence_processor, SETTINGS)
    detector.run()
    # After window is closed, speak the final sequence if needed
    if sequence_processor.sequence and SETTINGS['audio_enabled']:
        threading.Thread(target=sequence_processor.speak_final_sequence, daemon=True).start()

def settings():
    settings_window = Toplevel(home)
    settings_window.title("Settings")
    settings_window.geometry("400x300")
    settings_window.resizable(False, False)

    # Language Selection
    Label(settings_window, text="Select Language:", font=('Arial', 12)).pack(pady=10)
    
    # Get the language name from the code
    current_lang_name = "English"  # Default
    for name, code in SUPPORTED_LANGUAGES.items():
        if code == SETTINGS['language']:
            current_lang_name = name
            break
            
    language_var = StringVar(value=current_lang_name)
    language_combo = ttk.Combobox(settings_window, textvariable=language_var, 
                                 values=list(SUPPORTED_LANGUAGES.keys()))
    language_combo.pack(pady=5)

    # Audio Toggle
    audio_var = BooleanVar(value=SETTINGS['audio_enabled'])
    audio_check = Checkbutton(settings_window, text="Enable Audio", 
                             variable=audio_var, font=('Arial', 12))
    audio_check.pack(pady=10)

    def save_settings():
        SETTINGS['language'] = SUPPORTED_LANGUAGES[language_combo.get()]
        SETTINGS['audio_enabled'] = audio_var.get()
        
        # Save settings to file
        with open('settings.json', 'w') as f:
            json.dump(SETTINGS, f)
        
        # Update sequence processor settings
        sequence_processor.settings = SETTINGS
        
        settings_window.destroy()
        tkMessageBox.showinfo("Success", "Settings saved successfully!")

    Button(settings_window, text="Save", command=save_settings, 
           font=('Arial', 12)).pack(pady=20)

def about():
    tkMessageBox.showinfo(
        'About Us', Sign to Text and Speech is an innovative application that bridges communication gaps by translating sign language into text and speech in real-time. It supports both alphabets and common words/phrases, making it a versatile tool for sign language users.

Features:
- Real-time sign language detection
- Support for both alphabets and common phrases
- Multi-language speech output
- Adjustable settings for personalization
- User-friendly interface
- Sequence processing to build sentences
- Text translation in multiple Indian languages

This application aims to make communication more accessible and inclusive for the deaf and hard of hearing community.)
       
photo = Image.open(directory+"assets/1.jpeg")
img3 = ImageTk.PhotoImage(photo)
b2=Button(home, highlightthickness = 0, bd = 0,activebackground="#e4e4e4", image = img3,command=digitalpha)
b2.place(x=69,y=221)

photo = Image.open(directory+"assets/2.jpeg")
img2 = ImageTk.PhotoImage(photo)
b1=Button(home, highlightthickness = 0, bd = 0,activebackground="white", image = img2,command=yolo)
b1.place(x=69,y=330)

photo = Image.open(directory+"assets/3.jpeg")
img4 = ImageTk.PhotoImage(photo)
b1=Button(home, highlightthickness = 0, bd = 0,activebackground="white", image = img4,command=settings)
b1.place(x=71,y=438)

photo = Image.open(directory+"assets/4.png")
img5 = ImageTk.PhotoImage(photo)
b1=Button(home, highlightthickness = 0, bd = 0,activebackground="white", image = img5,command=about)
b1.place(x=71,y=531)

photo = Image.open(directory+"assets/5.png")
img6 = ImageTk.PhotoImage(photo)
b1=Button(home, highlightthickness = 0, bd = 0,activebackground="white", image = img6,command=Exit)
b1.place(x=385,y=531)

# Define save_sequence function before using it
def save_sequence():
    Save current sequence to a file
    if not sequence_processor.sequence:
        tkMessageBox.showinfo("Information", "No sequence to save.")
        return
        
    sequence_text = sequence_processor.get_sequence()
    translated_text = sequence_processor.get_translated_text()
    
    # Create a directory for saved sequences if it doesn't exist
    os.makedirs("saved_sequences", exist_ok=True)
    
    # Generate a timestamp for the filename
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"saved_sequences/sequence_{timestamp}.txt"
    
    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Original: {sequence_text}\n")
        f.write(f"Translated: {translated_text}\n")
    
    tkMessageBox.showinfo("Success", f"Sequence saved to {filename}")

# Now create the button after the function is defined
save_button = Button(home, text="Save Sequence", command=save_sequence, 
                    font=('Arial', 12), bg="#4CAF50", fg="white", 
                    activebackground="#45a049", activeforeground="white",
                    padx=10, pady=5)
save_button.place(x=225, y=620)  # Adjust position as needed

home.mainloop()
"""

# main.py
import os
import time
import threading
import ctypes
from tkinter import *
from PIL import ImageTk, Image
import tkinter.messagebox as tkMessageBox

# Windows OpenCV camera fix (safe to keep)
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

from sequence_processor import SequenceProcessor

# detectors (must accept a SequenceProcessor instance)
from alphabet_landmarks import AlphabetDetector
from digit_detector import DigitDetector
from word_detector import WordDetector


# =====================================================
# GLOBALS
# =====================================================
sequence_processor = SequenceProcessor()
detector_running = False   # prevents multiple webcam access
_detector_lock = threading.Lock()


# =====================================================
# WINDOW SETUP
# =====================================================
home = Tk()
home.title("Sign To Text")

# DPI-awareness + center the window
try:
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    home.geometry(f"1200x720+{w//2-600}+{h//2-360}")
except Exception:
    # fallback geometry
    home.geometry("1200x720")
home.resizable(0, 0)


# =====================================================
# BACKGROUND IMAGE (safe load)
# =====================================================
_bg_path = os.path.join("assets", "home.jpeg")
try:
    bg_img = ImageTk.PhotoImage(Image.open(_bg_path))
    bg_label = Label(home, image=bg_img)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    bg_label.lower()
except Exception:
    # ignore if background missing
    pass


# =====================================================
# UTILITY
# =====================================================
def stop_detector():
    """Signal detectors to stop (UI-level). The detector threads will set detector_running False when they finish."""
    global detector_running
    with _detector_lock:
        detector_running = False


# =====================================================
# BUTTON ACTIONS
# =====================================================
def Exit():
    """Exit handler: stop detectors, shutdown TTS, then quit."""
    if not tkMessageBox.askyesno("Exit", "Are you sure you want to exit?"):
        return

    # Signal detectors to stop (if any)
    stop_detector()

    # Give detectors a tiny moment to clean up if they are closing windows
    time.sleep(0.2)

    # Gracefully stop TTS thread (SequenceProcessor provides this)
    try:
        # sequence_processor.shutdown_tts(wait=True) must exist in your sequence_processor
        sequence_processor.shutdown_tts(wait=True)
    except Exception:
        # if shutdown_tts is not present or fails, ignore but warn
        print("Warning: sequence_processor.shutdown_tts failed or not available.")

    # Destroy the UI
    try:
        home.destroy()
    except Exception:
        os._exit(0)


def _start_detector_thread(fn):
    """Helper to start a detector function in a daemon thread and manage the running flag."""
    global detector_running
    with _detector_lock:
        if detector_running:
            return
        detector_running = True

    def _runner():
        global detector_running
        try:
            fn()
        except Exception as e:
            # show error to user, keep main app alive
            print("Detector exception:", e)
            tkMessageBox.showerror("Detector Error", str(e))
        finally:
            # ensure flag resets when detector thread ends
            with _detector_lock:
                detector_running = False

    threading.Thread(target=_runner, daemon=True).start()


def detect_alphabets():
    """Detect alphabets only (landmark-based)."""
    # Pass the shared sequence_processor instance into detector
    _start_detector_thread(lambda: AlphabetDetector(sequence_processor).run())


def detect_digits():
    """Detect digits only (digit detector)."""
    _start_detector_thread(lambda: DigitDetector(sequence_processor).run())


def detect_words():
    """Detect words via YOLO word detector."""
    _start_detector_thread(lambda: WordDetector(sequence_processor).run())


def about():
    tkMessageBox.showinfo(
        "About",
        "Sign To Text\n\n"
        "• Alphabet recognition (landmark-based CNN)\n"
        "• Digit recognition (separate optimized model)\n"
        "• Word recognition using YOLOv8\n"
        "• Stable real-time gesture detection\n"
        "• Text-to-speech enabled\n\n"
        "Academic Project"
    )


def save_sequence():
    if not sequence_processor.sequence:
        tkMessageBox.showinfo("Info", "No sequence to save.")
        return

    os.makedirs("saved_sequences", exist_ok=True)
    filename = f"saved_sequences/sequence_{time.strftime('%Y%m%d-%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(sequence_processor.get_sequence())

    tkMessageBox.showinfo("Saved", f"Saved to {filename}")


# =====================================================
# BUTTON IMAGES (load safely; keep references to PhotoImage objects)
# =====================================================
def _load_image(path, fallback_text=None, size=None):
    try:
        img = Image.open(path)
        if size:
            img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        print(f"Warning: failed to load image {path}")
        if fallback_text:
            # create a small placeholder
            placeholder = Image.new("RGB", size or (100, 50), color=(200, 200, 200))
            return ImageTk.PhotoImage(placeholder)
        return None


btn_alpha_img = _load_image(os.path.join("assets", "1.png"), size=(120, 80))
btn_digit_img = _load_image(os.path.join("assets", "3.png"), size=(120, 80))
btn_word_img  = _load_image(os.path.join("assets", "2.jpeg"), size=(120, 80))
btn_about_img = _load_image(os.path.join("assets", "5.png"), size=(120, 80))
btn_exit_img  = _load_image(os.path.join("assets", "6.png"), size=(120, 80))


# =====================================================
# BUTTONS placement
# =====================================================
# If images failed to load, fall back to text buttons
if btn_alpha_img:
    Button(home, image=btn_alpha_img, bd=0, command=detect_alphabets).place(x=69, y=160)
else:
    Button(home, text="Detect Alphabets", bd=0, command=detect_alphabets).place(x=69, y=160)

if btn_digit_img:
    Button(home, image=btn_digit_img, bd=0, command=detect_digits).place(x=69, y=275)
else:
    Button(home, text="Detect Digits", bd=0, command=detect_digits).place(x=69, y=275)

if btn_word_img:
    Button(home, image=btn_word_img, bd=0, command=detect_words).place(x=69, y=400)
else:
    Button(home, text="Detect Words", bd=0, command=detect_words).place(x=69, y=400)

if btn_about_img:
    Button(home, image=btn_about_img, bd=0, command=about).place(x=71, y=531)
else:
    Button(home, text="About", bd=0, command=about).place(x=71, y=531)

if btn_exit_img:
    Button(home, image=btn_exit_img, bd=0, command=Exit).place(x=385, y=531)
else:
    Button(home, text="Exit", bd=0, command=Exit).place(x=385, y=531)


Button(
    home,
    text="Save Sequence",
    font=("Arial", 12),
    bg="#4CAF50",
    fg="white",
    activebackground="#45a049",
    command=save_sequence
).place(x=225, y=620)


Button(
    home,
    text="Speak Sentence",
    font=("Arial", 12),
    bg="#2196F3",
    fg="white",
    command=sequence_processor.speak_full_sequence
).place(x=225, y=580)


# Ensure TTS is shutdown when window is closed via window manager (X / Windows close button)
def _on_close():
    # stop detectors if running
    stop_detector()
    time.sleep(0.1)
    try:
        sequence_processor.shutdown_tts(wait=True)
    except Exception:
        pass
    try:
        home.destroy()
    except Exception:
        os._exit(0)


home.protocol("WM_DELETE_WINDOW", _on_close)

# Start UI
home.mainloop()


