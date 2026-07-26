"""Central registry for all AI models - MINIMAL VERSION"""

import os
import whisper
from deepface import DeepFace
import mediapipe as mp
from Backend.Models.eye_tracker import EyeTracker
from .emotion_detector import EmotionDetector 
# Module-level storage
stt = None
emotion_detector = None
eye_tracker = None
video_processor = None
audio_extractor = None


def load_all_models():
    """Load all AI models at startup"""
    global stt, emotion_detector, eye_tracker, video_processor, audio_extractor
    
    print("\n⏳ Loading AI models...\n")
    
    # 1. Whisper
    print("Whisper...")
    stt = whisper.load_model("small")
    print("     ✅")
    
    # 2. DeepFace
    print("EmotionDetector...")
    emotion_detector = EmotionDetector()
    
    # 3. MediaPipe
    print("MediaPipe...")
    model_path = "Backend/Models/face_landmarker.task"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Missing: {model_path}")
    
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode
    
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.IMAGE,
        num_faces=1
    )
    eye_tracker = EyeTracker()
    print("     ✅")
    print("Utilities...")
    from Utilities.audio_extract import AudioExtractor
    from Utilities.video_utils import VideoProcessor
    audio_extractor = AudioExtractor()
    video_processor = VideoProcessor()
    print("     ✅")
    
    print("\n✅ Ready!\n")


# Getters
def get_stt():
    if stt is None: raise RuntimeError("Models not loaded!")
    return stt

def get_emotion_detector():
    if emotion_detector is None: raise RuntimeError("Models not loaded!")
    return emotion_detector

def get_eye_tracker():
    if eye_tracker is None: raise RuntimeError("Models not loaded!")
    return eye_tracker

def get_audio_extractor():
    if audio_extractor is None: raise RuntimeError("Models not loaded!")
    return audio_extractor

def get_video_processor():
    if video_processor is None: raise RuntimeError("Models not loaded!")
    return video_processor