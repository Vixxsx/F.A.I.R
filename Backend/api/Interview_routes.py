"""Interview processing routes"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from scipy import stats

# Import model registry
from Models import _registry as model_registry

router = APIRouter(prefix="/api/interview", tags=["interview"])

UPLOAD_DIR = "Data/Video/Raw"
FRAMES_DIR = "Data/Video/Frames"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)


def convert_numpy_types(obj):
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


@router.post("/analyze-answer")
async def analyze_answer(
    video: UploadFile = File(...),
    question: str = Form(...),
    questionNumber: int = Form(...)
):
    """Analyze interview answer"""
    
    # Get models from registry (safe at runtime)
    stt = model_registry.get_stt()
    emotion_detector = model_registry.get_emotion_detector()
    eye_tracker = model_registry.get_eye_tracker()
    audio_extractor = model_registry.get_audio_extractor()
    video_processor = model_registry.get_video_processor()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Save video
        video_path = os.path.join(UPLOAD_DIR, f"question_{questionNumber}_{timestamp}.webm")
        with open(video_path, "wb") as f:
            f.write(await video.read())
        
        print(f"\n{'='*60}")
        print(f"🎯 Analyzing Question {questionNumber}: {question[:50]}...")
        print(f"{'='*60}\n")
        
        print("🎤 Step 1: Extracting audio and transcribing...")
        audio_filename = f"temp_audio_{questionNumber}.wav"
        audio_path = audio_extractor.extract_audio(video_path, audio_filename)

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not created: {audio_path}")
        print(f"✅ Audio extracted: {audio_path}")
        transcript_result = stt.transcribe(audio_path)
        transcript_text = transcript_result["text"]
        print(f"Transript Text: '{transcript_text}'")
        print(f"Word Count: {transcript_result.get('word_count', 0)}")

        #stats = stt.get_speaking_stats(transcript_result)
        stats = {
            "total_words": transcript_result.get("word_count", 0),
            "duration_seconds": transcript_result.get("duration", 0),
            "speaking_time_seconds": transcript_result.get("duration", 0) * 0.8,
            "words_per_minute": (transcript_result.get("word_count", 0) / max(transcript_result.get("duration", 1), 1)) * 60
        }
        print(f"✅ Speaking stats: {stats['total_words']} words @ {stats['words_per_minute']:.0f} WPM")  
        # Step 2: Extract frames
        print("\n📸 Step 2: Extracting frames...")
        frames_output_dir = os.path.join(FRAMES_DIR, f"question_{questionNumber}_{timestamp}")
        os.makedirs(frames_output_dir, exist_ok=True)
        
        video_info = video_processor.get_video_info(video_path)
        duration = video_info.get("duration_seconds", 0)
        sample_every = max(1, int(duration))
        max_frames = min(20, max(5, int(duration / 6)))  # Dynamic frames
        
        frame_paths = video_processor.extract_frames(
            video_path,
            output_folder=frames_output_dir,
            every_nth=sample_every,
            max_frames=max_frames,
            return_arrays=True
        )
        print(f"✅ Extracted {len(frame_paths)} frames")
        
        # Step 3: Parallel emotion + eye tracking
        print("\n🖼️ Step 3: Analyzing emotions & eye contact (parallel)...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            eye_future = executor.submit(eye_tracker.analyze_frames_list, frame_paths)
            emotion_future = executor.submit(emotion_detector.analyze_frames_list, frame_paths)
            
            eye_results = eye_future.result()
            emotion_results = emotion_future.result()
        
        eye_summary = eye_results['summary']
        emotion_summary = emotion_results['summary']
        
        print(f"✅ Eye Contact: {eye_summary['avg_score']}/100")
        print(f"✅ Emotions: {emotion_summary['confidence_score']}/100")
        
        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Return response
        response = {
            "success": True,
            "question": question,
            "questionNumber": questionNumber,
            "transcript": transcript_text,
            "analysis": {
                "eye_contact": eye_summary,
                "emotions": emotion_summary,
                "speaking_stats": stats
            },
            "timestamp": timestamp
        }
        
        return convert_numpy_types(response)
        
    except Exception as e:
        print(f"\n❌ ANALYSIS FAILED: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def check_status():
    """Check if models are loaded"""
    return {
        "status": "ready",
        "models_loaded": model_registry.stt is not None
    }