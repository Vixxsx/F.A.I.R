"""
Central registry for all AI models.
Load once at startup, reuse everywhere.
"""

import os
import whisper
from deepface import DeepFace
import mediapipe as mp

# Module-level declarations
stt = None
filler_detector = None
emotion_detector = None
relevancy_analyzer = None
eye_tracker = None
video_processor = None
audio_extractor = None


def load_all_models():
    """Load all AI models at startup (only once)"""
    global stt, emotion_detector, eye_tracker, video_processor, audio_extractor
    
    print("\n⏳ Loading AI models (this may take 30-60 seconds)...\n")
    
    # 1. Load Whisper (Speech-to-Text)
    print("  📦 Loading Whisper (small model, 450MB)...")
    try:
        stt = whisper.load_model("medium")
        print("     ✅ Whisper loaded")
    except Exception as e:
        print(f"     ❌ Whisper failed: {e}")
        raise
    
    # 2. Load DeepFace (Emotion Detection)
    print("  📦 Loading DeepFace (emotion detection)...")
    try:
        emotion_detector = DeepFace.build_model(model_name="Emotion",task="facial_attribute")
        print("     ✅ DeepFace loaded")
    except Exception as e:
        print(f"     ❌ DeepFace failed: {e}")
        raise
    
    # 3. Load MediaPipe (Face Mesh / Eye Tracking)
    print("  📦 Loading MediaPipe (face mesh)...")
    try:
        model_path = "Backend/Models/face_landmarker.task"
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"❌ MediaPipe model not found: {model_path}\n"
                "This file must be in the repo. Do NOT download at runtime!"
            )
        
        BaseOptions = mp.tasks.BaseOptions
        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        
        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.IMAGE,
            num_faces=1
        )
        eye_tracker = FaceLandmarker.create_from_options(options)
        print("     ✅ MediaPipe loaded")
    except Exception as e:
        print(f"     ❌ MediaPipe failed: {e}")
        raise
    
    # 4. Initialize utilities
    print("  📦 Initializing utilities...")
    try:
        from Utilities.audio_extract import AudioExtractor
        from Utilities.video_utils import VideoProcessor
        
        audio_extractor = AudioExtractor()
        video_processor = VideoProcessor()
        print("     ✅ Utilities initialized")
    except Exception as e:
        print(f"     ❌ Utilities failed: {e}")
        raise
    
    print("\n✅ All models loaded successfully!\n")


def get_stt():
    """Get Whisper model"""
    if stt is None:
        raise RuntimeError("Models not loaded! Call load_all_models() first")
    return stt


def get_emotion_detector():
    """Get DeepFace model"""
    if emotion_detector is None:
        raise RuntimeError("Models not loaded! Call load_all_models() first")
    return emotion_detector


def get_eye_tracker():
    """Get MediaPipe model"""
    if eye_tracker is None:
        raise RuntimeError("Models not loaded! Call load_all_models() first")
    return eye_tracker


def get_audio_extractor():
    """Get audio extractor utility"""
    if audio_extractor is None:
        raise RuntimeError("Models not loaded! Call load_all_models() first")
    return audio_extractor


def get_video_processor():
    """Get video processor utility"""
    if video_processor is None:
        raise RuntimeError("Models not loaded! Call load_all_models() first")
    return video_processor